import json
from ai_writer import AIWriter

class NewsEditor:
    def __init__(self):
        self.writer = AIWriter()

    def review_batch(self, articles):
        """[V3.0 Global] 기사를 분석하여 EN/KO 동시 생성 및 테마 적합성 검증"""
        news_list_str = ""
        for i, article in enumerate(articles):
            news_list_str += f"[{i}] {article['title']}\n- 원문 내용: {article.get('description', '없음')}\n"

        prompt = f"""
        You are the Editor-in-Chief & Lead Tech Journalist of 'Lego-Sia Strategy Magazine' in April 2026.
        Your persona: A 15-year veteran in IT strategy and hardware analysis with a sharp, insightful editorial voice.

        [STRICT EDITORIAL WORKFLOW]
        STEP 1 (EN Refined - Expansion Mode): Write a SUBSTANTIAL professional news article in English.
          - ABSOLUTE RULE: Respect the source content. Never reduce or omit facts. Instead, EXPAND the source into a full feature by adding context, industry background, and 2026-specific analysis.
          - Length: At least 5 detailed paragraphs.
        STEP 2 (KO Localized - Contextual): Localize Step 1 into professional Korean.
          - Header 1 (Summary): "Executive Summary: 핵심 이슈 브리핑"
          - Header 2 (Main): "심층 분석: 글로벌 테크 리포트"
          - Header 3 (Insight): "Editorial: 미래 전략과 시장 전망"
          - Use a sophisticated, human-journalist tone. Avoid "AI" or "Migration" keywords in headers.

        [STRICT MISSION & RULES]
        1. THEMATIC GATEKEEPER (SUPER STRICT): Score < 8 means skip. Score 9+ is "Editor's Choice".
           - CATEGORICAL REJECTION (Score 0): K-Pop, BTS, Entertainment, Sports, Politics, Celeb Gossips.
        2. DATA VISUALIZATION: For any numeric data, timelines, or comparative points, ALWAYS use Markdown Tables to enhance professional readability.
        3. TITLES (STRICT): 'eng_title' and 'kor_title' MUST be within 50 characters (including spaces). Punchy and SEO-friendly.
        4. CATEGORY DIVERSITY: Do NOT default to "tech-biz".
        4. NO SHRINKAGE: Expand the content substantially (min 5 paragraphs).
        3. DUAL-LANGUAGE OUTPUT: Complete, long-form EN and KO versions are mandatory.
        4. IMAGE PROMPT: Unique 64-word artistic metaphor.
        5. CATEGORY: ["ai-tech", "ai-agents", "hardware", "game", "monetization", "tech-biz"].
        
        Return in JSON list format:
        [
          {{
            "index": 0,
            "score": 9,
            "category": "Corrected category (KO)",
            "eng_category": "Corrected category (EN)",
            "image_prompt": "Stylized metaphoric prompt...",
            "eng_title": "Punchy Tech Strategy Title (Max 50 chars)",
            "kor_title": "핵심을 찌르는 50자 이내의 한국어 제목",
            "keywords": ["tag1", "tag2", "tag3"],
            "eng_content": "Long-form professional English feature (Step 1). Min 5 paragraphs.",
            "kor_content": "글로벌 시장 맥락이 반영된 심층 한국어 본문 (Step 2). 최소 1,200자 이상.",
            "kor_summary": "1. 핵심요약\n2. 핵심요약\n3. 핵심요약",
            "kor_insight": "고급 비즈니스 인사이트 및 전략적 대응 가이드"
          }}
        ]

        NEWS BATCH (April 2026 Source):
        {json.dumps(articles, ensure_ascii=False)}
        """
        
        try:
            print(f"[*] AI Global Editor: Orchestrating Dual-Language (EN/KO) Masterpieces...")
            response_text = self.writer.generate_content(prompt, category="AI-글로벌편집장")
            
            if not response_text: return []

            # JSON 추출 로직 (v3.0 강화)
            clean_json = response_text
            if "```json" in response_text:
                clean_json = response_text.split("```json")[-1].split("```")[0].strip()
            
            start = clean_json.find("[")
            end = clean_json.rfind("]") + 1
            if start != -1 and end != -1:
                return json.loads(clean_json[start:end])
            return []
        except Exception as e:
            print(f"[ERROR] Global Deep-Editing failed: {e}")
            return []
