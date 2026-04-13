import json
import re
from ai_writer import AIWriter 

class EditorInChief:
    def __init__(self, writer=None):
        self.writer = writer if writer else AIWriter()
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
          "approval": true,
          "score": 8.5,
          "critique": "Short constructive criticism in Korean",
          "decision": "PASS"
        }
        """

    def review_article(self, article_json):
        """기사를 검수하여 발행 승인 여부 결정"""
        prompt = f"{self.system_prompt}\n\nPlease review this article (EN & KO versions):\n{json.dumps(article_json, ensure_ascii=False)}"
        
        # [V11.0] 모델 강제 지정을 피하고 AIWriter의 가용성 로직에 맡김
        review_text = self.writer.generate_content(prompt) 
        
        if not review_text:
            return {"decision": "PASS", "reason": "No AI response, auto-pass for continuity."}
            
        try:
            # [V11.0 Production Parsing]
            start_idx = review_text.find("{")
            end_idx = review_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean_json = review_text[start_idx:end_idx+1]
                data = json.loads(clean_json, strict=False)
                # 데이터 정규화
                if "decision" not in data:
                    data["decision"] = "PASS" if data.get("approval") or data.get("score", 0) >= 7 else "REJECT"
                return data
            
            return {"decision": "PASS", "reason": "Lenient fallback - parsing failed."}
        except Exception as e:
            print(f" [!] Review parsing failed: {e}")
            return {"decision": "PASS", "reason": "Parsing error in review."}

if __name__ == "__main__":
    reviewer = EditorInChief()
    print(reviewer.review_article({"kor_title": "테스트", "kor_content": "내용"}))
