import os
import requests
import json
import time
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AIWriter:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

    def _generate_content_logic(self, prompt, provider="gemini"):
        """실제 API 호출 로직 (Gemini 또는 OpenRouter)"""
        if provider == "gemini":
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            return model.generate_content(prompt).text
        else:
            # OpenRouter 최신 무료 라이우터 사용
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openrouter_key.strip()}"},
                data=json.dumps({"model": "openrouter/free", "messages": [{"role": "user", "content": prompt}]}),
                timeout=150
            )
            return response.json()["choices"][0]["message"]["content"]

    def generate_content(self, keyword, extra_info=""):
        # 고도로 정제된 한국어 전문가 프롬프트
        prompt = f"""
        당신은 대한민국 최고의 SEO 전문가이자 전업 블로거 'Lego-sia'입니다.
        당신의 목표는 "{keyword}"에 대해 구글 검색 결과 1위에 오를 수 있는 독보적인 고퀄리티 콘텐츠를 작성하는 것입니다.

        [중요: 작성 스타일 가이드]
        1. **완벽한 한국어**: 영어 단어를 괄호에 병기하거나(예: sized 합니다), 번역투의 문장을 절대 사용하지 마세요. 
           - 신뢰감이 느껴지는 전문적인 경어체(~입니다, ~아닐까 합니다)를 사용하세요.
        2. **풍부한 인사이트**: 뉴스 내용을 단순 나열하지 말고, 이것이 독자의 실생활이나 경제적 측면에 주는 '의미'와 '미래 전망'을 반드시 포함하세요.
        3. **가독성 극대화**: 마크다운의 표(Table), 인용구(Blockquote), 불렛 포인트를 활용해 잡지 기사처럼 구성하세요.
        4. **SEO 구성**: 제목은 자극적이지 않으면서도 클릭을 유도하는 '최신 가이드', '비밀', '전격 분석' 등의 단어를 적절히 사용하세요.

        [콘텐츠 구조]
        - 제목 (H1)
        - 도입부: 이 주제에 주목해야 하는 이유
        - 핵심 요약 (체크리스트 형태)
        - 심층 분석 (표 또는 단락 구분)
        - Lego-sia의 인사이트 (독자가 꼭 알아야 할 팁)
        - 결론 및 요약

        [주제 정보]
        - 주제: {keyword}
        - 참고: {extra_info}

        [Frontmatter 양식] - 반드시 이 형식으로 시작하세요.
        ---
        title: "제목"
        date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
        description: "SEO 최적화된 독창적인 요약 (150자)"
        categories: ["라이프스타일"]
        tags: ["정보", "트렌드", "2026"]
        slug: "news-{int(time.time())}"
        ---
        """
        
        try:
            print("[*] 1차 시도: Gemini Direct...")
            return self._generate_content_logic(prompt, "gemini")
        except Exception as e:
            print(f"[!] Gemini 실패({e}), 2차 OpenRouter 라우터 가동...")
            time.sleep(10)
            try:
                return self._generate_content_logic(prompt, "openrouter")
            except Exception as e2:
                print(f"[!] 전사적 시도 실패: {e2}")
                return None

    def save_post(self, content, filename):
        if not content: return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        posts_dir = os.path.join(base_dir, "content", "posts")
        os.makedirs(posts_dir, exist_ok=True)
        # AI가 멋대로 markdown 블록을 씌우는 경우 제거
        clean_content = content.replace("```markdown", "").replace("```", "").strip()
        with open(os.path.join(posts_dir, filename), "w", encoding="utf-8") as f:
            f.write(clean_content)

if __name__ == "__main__":
    pass
