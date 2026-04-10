import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()

def check_gemini():
    print("--- [Gemini Models] ---")
    key = os.getenv("GEMINI_API_KEY")
    try:
        genai.configure(api_key=key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}")
    except Exception as e:
        print(f"Error: {e}")

def check_openrouter():
    print("\n--- [OpenRouter Free Models] ---")
    key = os.getenv("OPENROUTER_API_KEY")
    try:
        response = requests.get(
            url="https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key}"}
        )
        models = response.json().get('data', [])
        for m in models:
            if m['id'].endswith(':free'):
                print(f"Free Model ID: {m['id']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_gemini()
    check_openrouter()
