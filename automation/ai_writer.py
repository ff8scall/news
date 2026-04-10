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

    def _generate_via_gemini(self, prompt):
        if not self.gemini_key: return None
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(prompt).text

    def _generate_via_openrouter(self, prompt):
        # 유저가 제공한 리스트 기반 최적의 무료 모델 추천순
        free_models = [
            "openrouter/free", # 1순위: 자동 라우터 (성공률 최고)
            "google/gemma-3-27b:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemma-3-12b:free"
        ]
        
        for model in free_models:
            print(f"[*] OpenRouter 시도 중: {model}")
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key.strip()}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://blog.lego-sia.com"
                    },
                    data=json.dumps({
                        "model": model, 
                        "messages": [{"role": "user", "content": prompt}]
                    }),
                    timeout=120
                )
                if response.status_code == 200:
                    res_json = response.json()
                    if "choices" in res_json:
                        return res_json["choices"][0]["message"]["content"]
                else:
                    print(f"    [!] {model} 실패 상태코드: {response.status_code}")
            except Exception as e:
                print(f"    [!] {model} 연결 시도 중 에러: {e}")
            time.sleep(2)
        
        return None

    def generate_content(self, keyword, extra_info=""):
        prompt = f"""
        당신은 상위 0.1% SEO 전문가 블로거입니다. 다음 주제로 유익한 Hugo 블로그 글을 한국어로 작성하세요.
        키워드: {keyword}
        참고자료: {extra_info}

        ---
        title: "제목"
        date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
        description: "SEO 요약"
        categories: ["라이프스타일"]
        tags: ["트렌드", "정보"]
        slug: "post-{int(time.time())}"
        ---
        본문 내용 (마크다운 형식으로 풍부하게 작성)
        """
        
        # 1. Gemini Direct 시도
        try:
            print("[*] 1차 시도: Gemini Direct...")
            content = self._generate_via_gemini(prompt)
            if content: return content
        except:
            print("[!] Gemini 실패, OpenRouter로 전환합니다.")

        # 2. OpenRouter 시도
        return self._generate_via_openrouter(prompt)

    def save_post(self, content, filename):
        if not content: return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        posts_dir = os.path.join(base_dir, "content", "posts")
        os.makedirs(posts_dir, exist_ok=True)
        path = os.path.join(posts_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[V] 포스팅 생성 완료: {path}")

if __name__ == "__main__":
    pass
