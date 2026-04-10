import json
from ai_writer import AIWriter

class NewsEditor:
    def __init__(self):
        self.writer = AIWriter()

    def review_batch(self, articles):
        """기사를 분석하여 한글 제목, 번역, 심층 분석을 반환하여 본문 풍성하게 함"""
        news_list_str = ""
        for i, article in enumerate(articles):
            news_list_str += f"[{i}] {article['title']}\n- 원문 내용: {article.get('description', '없음')}\n"

        prompt = f"""
        당신은 2026년 최고의 IT 테크 매거진 전문 편집장입니다. 
        제공된 영문 뉴스(제목 및 원문 내용)를 바탕으로 프리미엄 한글 포스팅을 구성하세요.

        [뉴스 목록]
        {news_list_str}
        
        [지시사항]
        1. 7점 이상 기사에 대해 다음을 작성하세요 (본문 분량 확보가 핵심):
           - "korean_title": 기사를 관통하는 전문적인 **한글 제목**.
           - "translation": 제공된 원문 내용을 자연스러운 한국어로 충실히 **번역**. (원문 훼손 금지)
           - "summary": 기사 핵심 포인트 3가지 요약.
           - "insight": 이 소식이 2026년 기술/경제 생태계에 줄 영향과 비즈니스 인사이트 (2~3문단, 300자 이상 권장).
        2. 반드시 아래 JSON 리스트 형식으로만 응답하세요.
        
        [
            {{
                "index": 0,
                "score": 9,
                "korean_title": "한글 제목",
                "translation": "원문 번역 내용",
                "summary": "1. 요약...\\n2. 요약...\\n3. 요약...",
                "insight": "심층 분석 및 전망 (본문의 메인이 되는 풍부한 내용)"
            }},
            ...
        ]
        """
        
        try:
            print(f"[*] AI Deep-Editing: Preserving original facts and enriching body content...")
            response_text = self.writer.generate_content(prompt, category="AI·프리미엄", model="models/gemini-1.5-flash-latest")
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            results = json.loads(clean_json)
            return results
        except Exception as e:
            print(f"[ERROR] AI Deep-Editing failed: {e}")
            return []
