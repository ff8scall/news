import json
from ai_writer import AIWriter

class NewsEditor:
    def __init__(self):
        self.writer = AIWriter()

    def review_article(self, article):
        """기사 가치 평가 및 3줄 요약 생성"""
        prompt = f"""
        당신은 IT/테크 전문 매거진의 편집장입니다. 다음 뉴스를 분석하여 형식에 맞춰 응답하세요.
        
        뉴스 제목: {article['title']}
        뉴스 출처: {article['source']}
        뉴스 URL: {article['url']}
        
        [지시사항]
        0. 현재 시점은 **2026년 4월**입니다. 모든 가치 수위는 이를 기준으로 합니다.
        1. 가치 평가(score): IT, AI, 신기술, 게임과 관련이 깊을수록 높은 점수를 주세요 (0~10).
           - 주의: 이미 1~2년이 지난 구형 기술(Blackwell, GPT-4, Llama 3 등)을 마치 '신규'인 것처럼 소개하는 글은 0점을 주어 탈락시키세요. 
        2. 기사 요약(summary): 바쁜 독자를 위해 존댓말로 정중하게 3줄 요약을 만드세요.
        3. 응답은 반드시 아래 JSON 형식으로만 하세요. 다른 말은 덧붙이지 마세요.
        
        {{
            "score": 8,
            "summary": "1. 첫 번째 요약 문장\\n2. 두 번째 요약 문장\\n3. 세 번째 요약 문장"
        }}
        """
        
        try:
            print(f"[*] AI Reviewing: {article['title'][:30]}...")
            response_text = self.writer.generate_content(prompt, category="AI·신기술")
            # JSON만 추출
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_json)
            return result
        except Exception as e:
            print(f"[ERROR] AI Review failed: {e}")
            return None
