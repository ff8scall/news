import os
import requests
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
load_dotenv('automation/.env')

def test_gemini():
    key = os.getenv("GEMINI_API_KEY")
    if not key: return "MISSING KEY"
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content("Say hello in 5 words.")
        return f"SUCCESS: {response.text.strip()}"
    except Exception as e:
        return f"FAILED: {e}"

def test_deepseek():
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key: return "MISSING KEY"
    try:
        res = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {key.strip()}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Say hello in 5 words."}],
                "max_tokens": 10
            }), timeout=10
        )
        if res.status_code == 200:
            return f"SUCCESS: {res.json()['choices'][0]['message']['content'].strip()}"
        else:
            return f"FAILED: Status {res.status_code} - {res.text}"
    except Exception as e:
        return f"FAILED: {e}"

def test_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key: return "MISSING KEY"
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key.strip()}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": "Say hello in 5 words."}],
                "max_tokens": 10
            }), timeout=10
        )
        if res.status_code == 200:
            return f"SUCCESS: {res.json()['choices'][0]['message']['content'].strip()}"
        else:
            return f"FAILED: Status {res.status_code} - {res.text}"
    except Exception as e:
        return f"FAILED: {e}"

def test_openrouter():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key: return "MISSING KEY"
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key.strip()}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say hello in 5 words."}]
            }), timeout=10
        )
        if res.status_code == 200:
            return f"SUCCESS: {res.json()['choices'][0]['message']['content'].strip()}"
        else:
            return f"FAILED: Status {res.status_code} - {res.text}"
    except Exception as e:
        return f"FAILED: {e}"

if __name__ == "__main__":
    print("=== AI PROVIDER DIAGNOSTIC TEST ===")
    print(f"1. Gemini:     {test_gemini()}")
    print(f"2. DeepSeek:   {test_deepseek()}")
    print(f"3. Groq:       {test_groq()}")
    print(f"4. OpenRouter: {test_openrouter()}")
    print("===================================")
