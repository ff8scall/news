import json
import re
import time
from ai_writer import AIWriter

class NewsEditor:
    def __init__(self, writer=None):
        self.writer = writer if writer else AIWriter()

    def review_batch(self, articles):
        """[V10.9] 개별 기사 처리로 리스크 분산 및 토큰 제한 극대화"""
        all_drafts = []
        for article in articles:
            prompt = f"""
            Task: Expand ONE tech news into a professional dual-language (EN/KO) feature.
            Identity: You are a senior tech strategist at a premium magazine.
            Rules: Use markdown, 5+ paragraphs per language, STRICT JSON.
            Focus: Analyze the 'Business Impact' and 'Market Outlook'. Provide sharp, strategic insights.
            
            JSON format: {{ "score": 10, "category": "ai-tech", "eng_title": "...", "kor_title": "...", "eng_content": "...", "kor_content": "...", "kor_summary": "...", "kor_insight": "비즈니스 임팩트: ... 전략적 전망: ..." }}
            
            Source Article:
            Title: {article['title']}
            Content: {article.get('description', '')}
            """
            try:
                res = self.writer.generate_content(prompt)
                if not res: continue
                
                start_idx = res.find("{")
                end_idx = res.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    clean_json = res[start_idx:end_idx+1]
                    try:
                        draft = json.loads(clean_json, strict=False)
                        # [V10.9] 카테고리 보정
                        cat = draft.get('category', 'tech-biz').lower()
                        if any(k in cat for k in ['ai', 'agent', '기술', '에이전트']): draft['category'] = 'ai-tech'
                        elif any(k in cat for k in ['hard', 'chip', 'semic', '하드']): draft['category'] = 'hardware'
                        elif any(k in cat for k in ['game', '플레이', '게임']): draft['category'] = 'game'
                        
                        all_drafts.append(draft)
                    except: continue
            except: continue
            time.sleep(15) 
        return all_drafts
