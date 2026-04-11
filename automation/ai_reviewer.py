import json
from ai_writer import AIWriter # 최신 AI 통합 엔진 활용

class EditorInChief:
    def __init__(self):
        self.writer = AIWriter()
        self.system_prompt = """
        Your Persona: A cynical, high-level Strategic Editor-in-Chief for a premium tech magazine.
        Your Mission: Review the article written by a journalist and decide if it is worthy of publication.
        
        [CRITICAL REVIEW CRITERIA]
        1. STRATEGIC VALUE: Does this provide deep insight or is it just fluff?
        2. TONE: Is it professional, cold, and calculated? Not "excited" or "AI-sounding".
        3. FACTUAL CONSISTENCY: Does the title match the content?
        4. E-E-A-T: Would a CEO trust this information?

        [OUTPUT FORMAT]
        Return ONLY a JSON object:
        {
          "approval": true/false,
          "score": 0.0 to 10.0,
          "critique": "Short constructive criticism in Korean",
          "suggested_fix": "Optional suggestion to improve if applicable"
        }
        """

    def review_article(self, article_json):
        """기사를 검수하여 발행 승인 여부 결정"""
        prompt = f"Please review this article (EN & KO versions):\n{json.dumps(article_json, ensure_ascii=False)}"
        # AIWriter의 통합 생성 메서드 호출
        response = self.writer.generate_content(prompt, model='models/gemini-1.5-pro-latest') 
        
        try:
            if not response: return {"approval": False, "score": 0, "critique": "AI Response Empty"}
            clean_res = response.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_res)
        except:
            return {"approval": False, "score": 0, "critique": "Parsing error in review."}

if __name__ == "__main__":
    # Test review
    reviewer = EditorInChief()
    print(reviewer.review_article({"kor_title": "테스트 기사", "kor_content": "너무 짧은 테스트 본문입니다."}))
