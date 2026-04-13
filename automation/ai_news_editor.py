import json
import os
import re
import time
import logging
from datetime import datetime
from ai_writer import AIWriter

# [V3.0] 로깅 설정
logger = logging.getLogger("LegoSia.NewsEditor")

# [V7.5] 용어 사전 (Glossary) - 오역 방지 및 전문성 강화
GLOSSARY = {
    "Anthropic": "앤트로픽(Anthropic)",
    "NVIDIA": "엔비디아(NVIDIA)",
    "Blackwell": "블랙웰(Blackwell)",
    "HBM": "HBM(고대역폭 메모리)",
    "LLM": "LLM(대규모 언어 모델)",
    "MoE": "MoE(전문가 혼합 모델)",
    "Foundry": "파운드리(위탁 생산)",
    "Startups": "스타트업",
    "Monetization": "수익화",
    "White Noise": "백색 소음"
}

NEWS_JSON_SCHEMA = """
{
    "score": 1~10,
    "cluster": "ai-models-tools",
    "category": "ai-models",
    "eng_title": "...",
    "eng_keywords": ["Keyword1", "Keyword2", "Brand", "Industry", "Trend"],
    "eng_content": "### Section Title\n\nContent...",
    "kor_title": "...",
    "kor_summary": ["핵심 포인트 1", "핵심 포인트 2"],
    "kor_keywords": ["개체명", "기술명", "트렌드", "전망", "가격/성능"],
    "kor_analysis_title": "Dyanmic keyword-rich subtitle (e.g., 'HBM4 기술의 성능 병목 해결')",
    "kor_content": "### 세부 부제\n\n본문...",
    "kor_insight_title": "Dynamic subtitle (e.g., '엔비디아의 독점 체제에 미칠 영향')",
    "kor_insight": "### 시사점\n\n전문적인 통찰..."
}
"""

SCORING_PROMPT = """
[TASK]: Score these news items from 1-10 based on Tech Innovation, Market Impact, and Global Relevance.
[OUTPUT]: Strictly JSON list of integers. (e.g., [8, 4, 9])
[ITEMS]:
"""

class NewsEditor:
    """[V7.5] 완성형 에디터: 용어 사전, 지능형 스코어링, 백로그 아카이브 탑재"""
    def __init__(self, writer=None):
        self.writer = writer if writer else AIWriter()
        self.authority_sources = ["Reuters", "TechCrunch", "Bloomberg", "The Verge", "CNBC", "Wired", "Engadget", "Digital Trends", "CNET"]

    def _apply_glossary(self, text):
        """[V0.2.6 Upgrade] 정규식 단어 경계(\b) 및 소제목 인용구 강제 치환"""
        if not text: return text
        
        # [Strategy] 긴 단어부터 치환하여 부분 일치 오류 방지
        sorted_keys = sorted(GLOSSARY.keys(), key=len, reverse=True)
        
        for eng in sorted_keys:
            kor = GLOSSARY[eng]
            pattern = re.compile(r'\b' + re.escape(eng) + r'(?!\s*\([^)]*\))', re.IGNORECASE)
            text = pattern.sub(kor, text)
            
        # [V0.2.6] 하위 소제목 강제 포맷팅 (인용구 스타일 고정)
        text = re.sub(r'^###\s+', '> ', text, flags=re.MULTILINE)
        text = re.sub(r'^####\s+', '> ', text, flags=re.MULTILINE)
        
        return text

    def _save_to_backlog(self, article, score):
        """[V7.1] 탈락된 기사를 백로그 파일에 보관"""
        try:
            archive_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
            os.makedirs(archive_dir, exist_ok=True)
            backlog_path = os.path.join(archive_dir, "backlog.json")
            
            backlog_data = []
            if os.path.exists(backlog_path):
                with open(backlog_path, "r", encoding="utf-8") as f:
                    try: backlog_data = json.load(f)
                    except: backlog_data = []
            
            if not any(item['url'] == article['url'] for item in backlog_data):
                article['selection_score'] = score
                article['archived_at'] = datetime.now().isoformat()
                backlog_data.append(article)
                with open(backlog_path, "w", encoding="utf-8") as f:
                    json.dump(backlog_data[-300:], f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Backlog Save Error: {e}")

    def _score_articles(self, articles):
        """[V7.0] 기사 선별 스코어러 - 고도화된 파싱 및 Fallback 적용"""
        if not articles: return []
        titles = [f"- {a['title']} ({a.get('source_name')})" for a in articles]
        prompt = SCORING_PROMPT + "\n".join(titles)
        res = self.writer.generate_content(prompt, role="processing")
        
        scores = []
        try:
            # 1. 표준적 JSON 배열 추출 시도
            match = re.search(r'\[(.*?)\]', res, re.DOTALL)
            if match:
                scores = json.loads(f"[{match.group(1)}]")
            else:
                # 2. 숫자만 콤마로 구분된 경우 추출 시도 (Fallback 1)
                # [V0.2.2 Fix] 1-10 사이의 독립된 숫자만 추출하여 모델명(5090 등) 간섭 방지
                numbers = re.findall(r'\b([1-9]|10)\b', res)
                scores = [int(n) for n in numbers]
        except Exception as e:
            logger.warning(f"Score Parsing Error: {e}")
            # 3. 모든 파싱 실패 시 기본 점수 부여 (Fallback 2)
            scores = [7] * len(articles)

        final_selection = []
        for i, article in enumerate(articles):
            score = scores[i] if i < len(scores) else 7
            source = article.get('source_name', '')
            is_authority = any(src.lower() in source.lower() for src in self.authority_sources)
            
            if score >= 7 or (score >= 5 and is_authority):
                final_selection.append(article)
            else:
                self._save_to_backlog(article, score)
                
        return final_selection if final_selection else [articles[0]]

    def _is_cached(self, query):
        """[V7.8] 12시간 내 동일 쿼리 중복 분석 방지용 캐시"""
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".news_cache")
        now = time.time()
        
        cache_data = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f: cache_data = json.load(f)
            except: pass
        
        # 12시간(43200초) 이내면 캐시 히트
        if query in cache_data and (now - cache_data[query]) < 43200:
            return True
            
        # 캐시 갱신
        cache_data[query] = now
        with open(cache_path, "w") as f: json.dump(cache_data, f)
        return False

    def _get_full_event_analysis(self, articles):
        # [V7.8] 캐시 체크로 API 낭비 철저 차단
        query_sig = articles[0]['title'][:30]
        if self._is_cached(query_sig):
            logger.info(f" [CACHE HIT] Already analyzed: {query_sig}")
            return None

        # [V7.0] 우수 기사 선별 후 분석 진행
        selected = self._score_articles(articles)
        if not selected: return None
        truncated = []
        for a in selected:
            content = a.get('description', a.get('content', ''))[:1000]
            truncated.append(f"Source: {a.get('source_name')}\nTitle: {a['title']}\nContent: {content}")
        combined_text = "\n---\n".join(truncated)
        prompt = f"[TASK]: Create a detailed English Tech Report synthesize from these: \n{combined_text}"
        return self.writer.generate_content(prompt, role="processing")

    def _extract_json_safe(self, text):
        if not text: return None
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try: return json.loads(match.group(), strict=False)
            except: pass
        return None

    def review_batch(self, articles, recent_posts=None):
        try:
            event_report_en = self._get_full_event_analysis(articles)
            if not event_report_en or len(event_report_en) < 300: return []

            history_context = ""
            if recent_posts:
                titles = [p.get('title', '') for p in recent_posts[:10]]
                history_context = f"\n[CONTEXT: RECENTLY PUBLISHED TITLES]\n- {chr(10)+'- '.join(titles)}\n"

            localize_prompt = f"""
            [PERSONA]: Senior Technical Journalist & Strategic Analyst.
            [TASK]: Localize the English report into a professional Korean tech paper. 
            {history_context}
            [STRICT RULES]: 
            1. 100% Korean Integrity. No Gibberish. Professional Journalism Tone.
            2. CATEGORY SELECTION: Choose EXACTLY ONE from: [ai-models, ai-tools, gpu-chips, pc-robotics, game-optimization, ai-gameplay, tutorials, compare]. 
               - [ai-models]: For broad AI trends, industrial strategy, market analysis, and LLM updates. (e.g., 'AI energy market crisis' belongs here!)
               - [ai-tools]: ONLY for specific software, apps, or 'how-to' use a single tech tool.
               - [compare]: For direct VS tests or tool/hardware head-to-heads (e.g., RTX 5090 vs 4090).
            3. FORMATTING (STRICT [V5.1]): 
               - DO NOT USE '###' for subheadings. 
               - USE '> Subtitle Text' (blockquote style) for ALL subheadings/titles.
            4. READABILITY (STRICT):
               - NEVER write long paragraphs. 
               - MAX 2 SENTENCES PER PARAGRAPH. 
               - USE DOUBLE NEWLINES (\n\n) FREQUENTLY. 
               - Keep each sentence concise. Break complex sentences.
            5. CONTENT DENSITY: Each section under a subheading MUST contain at least 4-5 substantial sentences (broken into 2 paragraphs). Deep contextual 'WHY' and 'HOW' only. 

            [OUTPUT STRUCTURE]: {NEWS_JSON_SCHEMA}
            [REPORT CONTEXT]: {event_report_en}
            """
            
            res = self.writer.generate_content(localize_prompt, role="writing")
            draft = self._extract_json_safe(res)
            
            if draft:
                # [V0.3.2 Post-Processing] Force line-break sanity to prevent long blocks
                for field in ['kor_content', 'kor_insight']:
                    if draft.get(field):
                        # Use regex to convert single space after sentence to double newline
                        draft[field] = re.sub(r'([.!?])\s+', r'\1\n\n', draft[field])
                
                # [V7.5] 용어 사전 최종 적용 및 정제
                draft['kor_title'] = self._apply_glossary(draft.get('kor_title', ''))
                draft['kor_content'] = self._apply_glossary(draft.get('kor_content', ''))
                draft['kor_insight'] = self._apply_glossary(draft.get('kor_insight', ''))
                
                draft['eng_content'] = event_report_en 
                cat = draft.get('category', 'ai-models')
                cluster_map = {
                    "ai-models": "ai-models-tools", "ai-tools": "ai-models-tools",
                    "gpu-chips": "gpu-hardware", "pc-robotics": "gpu-hardware",
                    "game-optimization": "ai-gaming", "ai-gameplay": "ai-gaming",
                    "tutorials": "guides", "compare": "ai-models-tools"
                }
                draft['cluster'] = cluster_map.get(cat, "ai-models-tools")
                draft['original_url'] = articles[0]['url']
                draft['original_image_url'] = articles[0].get('image')
                draft['source_name'] = articles[0].get('source_name', 'Global Sources')
                return [draft]
                
        except Exception as e:
            logger.error(f"NewsEditor Error: {e}")
        return []
