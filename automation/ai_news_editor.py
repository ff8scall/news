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
    "eng_title": "Brief English Title",
    "eng_description": "SEO-optimized 1-2 sentence English description",
    "eng_summary": "1-sentence highlight",
    "eng_keywords": ["Keyword1", "Keyword2"],
    "eng_content": "## Section Title\n\nFull English Content...",
    "kor_title": "한국어 제목",
    "kor_description": "SEO 최적화된 1-2문장 한국어 설명",
    "kor_summary": ["핵심 포인트 1", "핵심 포인트 2"],
    "kor_keywords": ["키워드1", "키워드2"],
    "kor_analysis_title": "Dynamic subtitle for analysis",
    "kor_content": "## Section Subtitle\n\nFull Korean analysis body...",
    "kor_insight_title": "인사이트 비평",
    "kor_insight": "## 시사점\n\nDeep analytical insight (minimum 3 sentences)...",
    "image_prompt_core": "A symbolic tech visual description"
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

    def _score_articles(self, articles, model=None):
        """[V7.0] 기사 선별 스코어러 - 고도화된 파싱 및 Fallback 적용"""
        if not articles: return []
        titles = [f"- {a['title']} ({a.get('source_name')})" for a in articles]
        prompt = SCORING_PROMPT + "\n".join(titles)
        res = self.writer.generate_content(prompt, role="processing", model=model)
        
        scores = []
        try:
            match = re.search(r'\[(.*?)\]', res, re.DOTALL)
            if match:
                scores = json.loads(f"[{match.group(1)}]")
            else:
                numbers = re.findall(r'\b([1-9]|10)\b', res)
                scores = [int(n) for n in numbers]
        except Exception as e:
            logger.warning(f"Score Parsing Error: {e}")
            scores = [7] * len(articles)

        final_selection = []
        for i, article in enumerate(articles):
            score = scores[i] if i < len(scores) else 7
            source = article.get('source_name', '')
            is_authority = any(src.lower() in source.lower() for src in self.authority_sources)
            is_valid_score = isinstance(score, (int, float))
            if is_valid_score and (score >= 7 or (score >= 5 and is_authority)):
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
        if query in cache_data and (now - cache_data[query]) < 43200:
            return True
        cache_data[query] = now
        with open(cache_path, "w") as f: json.dump(cache_data, f)
        return False

    def _get_full_event_analysis(self, articles, model=None):
        query_sig = articles[0]['title'][:30]
        # [DISABLED] Forcing re-generation for quality tuning
        # if self._is_cached(query_sig):
        #     logger.info(f" [CACHE HIT] Already analyzed: {query_sig}")
        #     return None

        selected = self._score_articles(articles, model=model)
        if not selected: return None
        truncated = []
        for a in selected:
            content = a.get('description', a.get('content', ''))[:1000]
            truncated.append(f"Source: {a.get('source_name')}\nTitle: {a['title']}\nContent: {content}")
        combined_text = "\n---\n".join(truncated)
        prompt = f"""
        [TASK]: Create a professional English Tech Analysis Report.
        [REQUIREMENTS]: 
         - Go beyond simple summary. Explain the "Why" and "So What".
         - Identify specific technical specs, market competitors, and potential business risks.
         - Use a cold, analytical tone like a Bloomberg or Reuters tech analyst.
        [INPUT DATA]: 
        {combined_text}
        """
        return self.writer.generate_content(prompt, role="processing", model=model)

    def _extract_json_safe(self, text):
        if not text: return None
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try: return json.loads(match.group(), strict=False)
            except: pass
        return None

    def review_batch(self, articles, recent_posts=None, model=None, hint_category=None):
        try:
            event_report_en = self._get_full_event_analysis(articles, model=model)
            if not event_report_en or len(event_report_en) < 200: return []

            history_context = ""
            if recent_posts:
                titles = [p.get('title', '') for p in recent_posts[:10]]
                history_context = f"\n[CONTEXT: RECENTLY PUBLISHED TITLES]\n- {chr(10)+'- '.join(titles)}\n"

            hint_str = f"\n[HINT]: The suggested category is '{hint_category}'. Stay accurate to this if possible." if hint_category else ""

            localize_prompt = f"""
            [PERSONA]: Tech News Editor & Technical Analyst.
            [TASK]: Localize the English report into a professional Korean tech article.
            {hint_str}
            {history_context}
            [QUALITY & TONE]:
             - **NO AI FILLER**: "매우 중요한 전환점이다", "기대를 모으고 있다", "성장이 기대된다" 같은 뻔한 문구는 절대 사용 금지.
             - **CRITICAL PERSPECTIVE**: 기사 내용의 이면을 파고들 것. 예를 들어, 소비자에게 이득이지만 기업에게는 독이 되는 구조나, 경쟁사(AMD, NVIDIA, Apple 등)와의 구체적인 대결 구도를 언급할 것.
             - **PROFESSIONAL DEPTH**: 기술 용어를 정확히 사용하되(예: 리소그래피, IPC 향상, 수율 등), 그 기술이 실제 사용자 경험에 어떻게 직결되는지 서술할 것.
            [STRICT RULES]: 
             1. KOREAN ONLY: 'kor_' 필드에는 100% 한글(Hangul)만 사용. (영어 병기 금지, 한자 금지)
             2. PARAGRAPH STRUCTURE: 문장을 짧게 끊지 말고, 3~4문장이 논리적으로 연결된 하나의 완성된 문단(Paragraph)을 구성할 것.
             3. CONCLUSION: "앞으로 지켜봐야 할 것이다" 식의 모호한 결론 대신, 독자가 얻어갈 수 있는 명확한 '인사이트 한 줄'로 마무리할 것.

            [OUTPUT STRUCTURE]: {NEWS_JSON_SCHEMA}
            [REPORT CONTEXT]: {event_report_en}
            """
            res = self.writer.generate_content(localize_prompt, role="writing", model=model)
            draft = self._extract_json_safe(res)
            
            if draft:
                for field in ['kor_content', 'kor_insight']:
                    if draft.get(field):
                        draft[field] = re.sub(r'([.!?])\s+', r'\1\n\n', draft[field])
                
                draft['kor_title'] = self._apply_glossary(draft.get('kor_title', ''))
                draft['kor_content'] = self._apply_glossary(draft.get('kor_content', ''))
                draft['kor_insight'] = self._apply_glossary(draft.get('kor_insight', ''))
                
                draft['eng_content'] = event_report_en 
                
                # [Sanity Check] Category & Cluster Alignment
                cat = draft.get('category', hint_category if hint_category else 'ai-models')
                # Ensure the category is valid
                valid_cats = ["ai-models", "ai-tools", "gpu-chips", "pc-robotics", "game-optimization", "ai-gameplay", "tutorials", "compare"]
                if cat not in valid_cats: cat = hint_category if hint_category in valid_cats else "ai-models"
                
                cluster_map = {
                    "ai-models": "ai-models-tools", "ai-tools": "ai-models-tools",
                    "gpu-chips": "gpu-hardware", "pc-robotics": "gpu-hardware",
                    "game-optimization": "ai-gaming", "ai-gameplay": "ai-gaming",
                    "tutorials": "guides", "compare": "guides"
                }
                draft['category'] = cat
                draft['cluster'] = cluster_map.get(cat, "ai-models-tools")
                draft['original_url'] = articles[0]['url']
                draft['original_image_url'] = articles[0].get('image')
                draft['source_name'] = articles[0].get('source_name', 'Global Sources')
                return [draft]
                
        except Exception as e:
            logger.error(f"NewsEditor Error: {e}")
        return []
