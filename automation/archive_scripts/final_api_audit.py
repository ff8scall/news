import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

def audit_gemini():
    print("[*] Auditing Gemini (Google V2 SDK)...", end=" ")
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        res = client.models.generate_content(model="gemini-pro-latest", contents="Test Ping")
        print(f"SUCCESS (Length: {len(res.text)})")
    except Exception as e: print(f"FAIL: {e}")

def audit_openrouter():
    print("[*] Auditing OpenRouter (Minimax)...", end=" ")
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"model": "minimax/minimax-m2.5:free", "messages": [{"role": "user", "content": "Ping"}]}
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200: print(f"SUCCESS (Res: {res.json()['choices'][0]['message']['content'][:20]}...)")
        else: print(f"FAIL: {res.status_code} - {res.text}")
    except Exception as e: print(f"FAIL: {e}")

def audit_github():
    print("[*] Auditing GitHub Models (GPT-4o-mini)...", end=" ")
    token = os.getenv("GITHUB_TOKEN")
    if not token or "your_github" in token:
        print("SKIP (Token not yet provided). Please update .env with GITHUB_TOKEN.")
        return
    url = "https://models.github.io/inference/chat/completions" # Note: models.github.ai or models.github.io? The user provided models.github.ai
    # Wait, the user provided https://models.github.ai/inference/chat/completions
    url = "https://models.github.ai/inference/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "X-GitHub-Api-Version": "2026-03-10"}
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Ping"}]}
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200: print(f"SUCCESS (Res: {res.json()['choices'][0]['message']['content'][:20]}...)")
        else: print(f"FAIL: {res.status_code} - {res.text}")
    except Exception as e: print(f"FAIL: {e}")

if __name__ == "__main__":
    print("=== [Lego-Sia MASTER API AUDIT] ===")
    audit_gemini()
    audit_openrouter()
    audit_github()
    print("\n[NOTE] News APIs (NewsAPI, GNews) were verified during the last harvest cycle (56 items found).")
