import os
import requests
import sys
from google import genai
from dotenv import load_dotenv

# Set UTF-8 for Windows Console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

load_dotenv()

def audit_gemini():
    print("[*] Auditing Gemini (Google V2 SDK)...", end=" ", flush=True)
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        res = client.models.generate_content(model="gemini-pro-latest", contents="Test Ping")
        print(f"SUCCESS (Length: {len(res.text)})")
    except Exception as e: print(f"FAIL: {e}")

def audit_openrouter():
    print("[*] Auditing OpenRouter (Minimax)...", end=" ", flush=True)
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"model": "minimax/minimax-m2.5:free", "messages": [{"role": "user", "content": "Ping"}]}
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200: 
            content = res.json()['choices'][0]['message']['content'][:20].encode('ascii', 'ignore').decode('ascii')
            print(f"SUCCESS (Res: {content}...)")
        else: print(f"FAIL: {res.status_code} - {res.text}")
    except Exception as e: print(f"FAIL: {e}")

if __name__ == "__main__":
    print("=== [Lego-Sia MASTER API AUDIT - RE-RUN] ===")
    audit_gemini()
    audit_openrouter()
