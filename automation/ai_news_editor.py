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
                        # [V13.0] 고도화된 카테고리 보정 (3개 클러스터 구조 지원)
                        cat = draft.get('category', 'tech-biz').lower()
                        text_pool = f"{cat} {draft.get('kor_title', '')} {draft.get('eng_title', '')}".lower()
                        
                        # [V13.1] 분류 우선순위 고도화: 구체적 카테고리 우선 매칭
                        if any(k in text_pool for k in ['agent', '에이전트']): draft['category'] = 'ai-agents'
                        elif any(k in text_pool for k in ['hard', 'chip', 'hw', '컴퓨팅', '하드웨어', '반도체']): draft['category'] = 'hardware'
                        elif any(k in text_pool for k in ['game', '플레이', '게임', 'gaming', 'unreal', '닌텐도']): draft['category'] = 'gaming'
                        elif any(k in text_pool for k in ['strategy', '전략', '수익', 'monetization']): draft['category'] = 'monetization'
                        elif any(k in text_pool for k in ['biz', '비즈니스', 'trend', '시장', '동향']): draft['category'] = 'tech-biz'
                        elif any(k in text_pool for k in ['ai', '기술', 'insight', '인텔리전스']): draft['category'] = 'ai-tech'
                        else: draft['category'] = 'ai-tech' # Final Fallback
                        
                        # [V12.1] 원본 메타데이터 보존 (이미지 및 주소 유실 방지)
                        draft['original_image_url'] = article.get('urlToImage')
                        draft['original_url'] = article.get('url')
                        
                        all_drafts.append(draft)
                    except: continue
            except: continue
            time.sleep(15) 
        return all_drafts
