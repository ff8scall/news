import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

class EmergencyWriter:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    def generate(self, prompt):
        print(f"[*] Calling Llama 3.1 Free via OpenRouter: {prompt[:30]}...")
        headers = {"Authorization": f"Bearer {self.api_key.strip()}"}
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "system", "content": "너는 IT 전문 기자다. 반드시 자연스럽고 정중한 한국어 존댓말로 뉴스 기사 형식을 갖춰 작성하라. 절대 영어를 섞지 마라."},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(payload), timeout=180)
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"[ERROR] {e}")
            return None

    def save(self, content, folder, filename):
        path = f"content/posts/{folder}"
        os.makedirs(path, exist_ok=True)
        # Markdown clean
        clean = content.replace("```markdown", "").replace("```", "").strip()
        with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
            f.write(clean)

def main():
    writer = EmergencyWriter()
    topics = [
        ("NVIDIA Blackwell GPU Industry Impact Analysis", "ai-tech"),
        ("Successful AI News Flipping & Monetization Strategy", "profit"),
        ("Next Generation Multi-Agent AI with AutoGen", "ai-agents")
    ]
    
    for title, folder in topics:
        print(f"\n[!] Re-writing masterpiece: {title}")
        prompt = f"다음 주제에 대해 전문적인 한국어 IT 뉴스 기사를 마크다운 형식으로 작성해줘: {title}. 제목, 일시, 카테고리, 요약, 상세 본문을 포함해."
        content = writer.generate(prompt)
        if content:
            fname = f"best-{int(time.time())}.md"
            writer.save(content, folder, fname)
            print(f"[SUCCESS] Saved to {folder}/{fname}")
        time.sleep(10)

if __name__ == "__main__":
    main()
