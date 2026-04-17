import google.generativeai as genai
import os
from dotenv import load_dotenv

# 스크립트 위치 기준으로 .env 로드
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("=== Available Models ===")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
