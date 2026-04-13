import json
import os
import re
import logging
from ai_writer import AIWriter

# [V3.0] 로깅 설정
logger = logging.getLogger("LegoSia.NewsEditor")

NEWS_JSON_SCHEMA = """
{
    "score": 1~10,
    "cluster": "Intelligence",
    "category": "...",
    "eng_title": "...",
    "eng_keywords": ["Keyword1", "Keyword2", "Brand", "Industry", "Trend"],
    "eng_content": "### Section Title\n\nContent...",
    "kor_title": "...",
    "kor_summary": ["핵심 포인트 1", "핵심 포인트 2"],
    "kor_keywords": ["개체명", "기술명", "트렌드", "전망", "가격/성능"],
    "kor_analysis_title": "Dyanmic keyword-rich subtitle for technical analysis (e.g., 'HBM4 기술의 성능 병목 해결')",
    "kor_content": "### 세부 부제\n\n**핵심데이터**를 포함한 본문...",
    "kor_insight_title": "Dynamic subtitle for strategic outlook (e.g., '엔비디아의 독점 체제에 미칠 영향')",
    "kor_insight": "### 시사점\n\n전문적인 통찰..."
}
"""

class NewsEditor:
    """[V3.0] 프로덕션 에디터: 스택 파서 및 지능형 중복 방지 탑재"""
    def __init__(self, model_name="gemini-2.0-flash", writer=None):
        self.model_name = model_name
        self.writer = writer if writer else AIWriter()

    def _extract_json_safe(self, text):
        """[V3.0 Stable] 스택 기반 JSON 추출기: 중첩 및 그리디 매칭 해결"""
        if not text: return None
        stack = []
        start = -1
        for i, char in enumerate(text):
            if char == '{':
                if start == -1: start = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        try:
                            return json.loads(text[start:i+1], strict=False)
                        except: return None
        return None

    def _get_full_event_analysis(self, articles):
        truncated = []
        for a in articles:
            content = a.get('description', a.get('content', ''))[:1000]
            truncated.append(f"Source: {a.get('source_name')}\nTitle: {a['title']}\nContent: {content}")
        
        combined_text = "\n---\n".join(truncated)
        prompt = f"""
        [TASK]: As a Senior Strategic Analyst, create a detailed English Tech Report synthesize from these sources.
        [SOURCES]:
        {combined_text}
        """
        return self.writer.generate_content(prompt, model=self.model_name)

    def review_batch(self, articles, recent_posts=None):
        """[V3.0] 중복 방지 컨텍스트 실제 주입 로직"""
        try:
            event_report_en = self._get_full_event_analysis(articles)
            if not event_report_en or len(event_report_en) < 300: return []

            # [V3.0 Fix] 최근 포스팅 제목 주입하여 중복 방지 강화
            history_context = ""
            if recent_posts:
                titles = [p.get('title', '') for p in recent_posts[:10]]
                history_context = f"\n[CONTEXT: RECENTLY PUBLISHED TITLES]\n- {chr(10)+'- '.join(titles)}\n"

            localize_prompt = f"""
            [PERSONA]: Senior Technical Journalist & Strategic SEO Specialist.
            [TASK]: Localize the English report into a premium Korean tech briefing optimized for search visibility.
            {history_context}
            
            [STRICT SEO & FORMATTING GUIDE]:
            1. TITLE: Create a CTR-optimized yet professional title containing the core subject.
            2. DYNAMIC SUBTITLES (NEW): DO NOT use generic '기술 분석'. Instead, create keyword-rich subtitles in 'kor_analysis_title' and 'kor_insight_title'.
            3. TAGS (EXPANDED): Provide 5-10 tags. Include: [Primary Entity (Brand/Product), Technology Category, Trend/Market Keywords].
            4. PARAGRAPHS: Double newline (\\n\\n) spacing is MANDATORY.
            5. VISUALS: Use **bold** for critical names, numbers, or technical specs to improve scannability.
            6. SUB-HEADINGS: Use '###' for detailed sub-sections within the content fields.
            7. LANGUAGE: Ensure 100% Korean integrity. No English headings in Korean fields.

            [OUTPUT STRUCTURE - STRICT JSON]:
            {NEWS_JSON_SCHEMA}
            
            [STRICT CATEGORY RULE]:
            - You MUST choose 'category' ONLY from this list: [llm-tech, ai-agent, ai-policy, future-sw, semi-hbm, hpc-infra, robotics, monetization, startups-vc, market-trend, game-tech, spatial-tech]
            
            [REPORT CONTEXT]:
            {event_report_en}
            """
            
            res = self.writer.generate_content(localize_prompt, model=self.model_name)
            draft = self._extract_json_safe(res)
            
            if draft:
                draft['eng_content'] = event_report_en 
                cluster_map = {
                    "llm-tech": "Intelligence", "ai-agent": "Intelligence", "ai-policy": "Intelligence", "future-sw": "Intelligence",
                    "semi-hbm": "Physical", "hpc-infra": "Physical", "robotics": "Physical",
                    "monetization": "Strategy", "startups-vc": "Strategy", "market-trend": "Strategy",
                    "game-tech": "Digital", "spatial-tech": "Digital"
                }
                cat = draft.get('category', 'ai-tools')
                draft['cluster'] = cluster_map.get(cat, "Intelligence")
                draft['original_url'] = articles[0]['url']
                draft['original_image_url'] = articles[0].get('image')
                draft['source_name'] = articles[0].get('source_name', 'Global Sources')
                return [draft]
                
        except Exception as e:
            logger.error(f"NewsEditor Error: {e}")
            
        return []
