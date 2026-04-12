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
    "cluster": "Intelligence | CoreTech | Strategy | Digital",
    "category": "...",
    "eng_title": "...",
    "eng_summary": "...",
    "eng_keywords": ["tag1", "tag2"],
    "eng_content": "Full English analysis",
    "kor_title": "...",
    "kor_summary": ["..."],
    "kor_keywords": ["키워드1", "키워드2"],
    "kor_content": "...",
    "kor_insight": "..."
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
            [PERSONA]: Senior Tech Editor.
            [TASK]: Localize the English report into a premium Korean tech briefing.
            {history_context}
            [STYLE]: DO NOT repeat topics covered in the recent titles above. 
            
            [OUTPUT STRUCTURE - STRICT JSON]:
            {NEWS_JSON_SCHEMA}
            
            [STRICT RULE]:
            - You MUST choose 'category' ONLY from this list: [llm-tech, ai-agent, ai-policy, future-sw, semi-hbm, hpc-infra, robotics, monetization, startups-vc, market-trend, game-tech, spatial-tech]
            - DO NOT invent new category names.
            
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
