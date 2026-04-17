import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("=== [Google GenAI V2 SDK Model List] ===")
try:
    # List models
    for model in client.models.list():
        # Check if it supports generateContent
        if 'generateContent' in model.supported_generation_methods:
            print(f"ID: {model.name} | Display: {model.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\n=== [Testing Connectivity] ===")
test_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-3.1-pro-preview"]
for m in test_models:
    try:
        print(f"Testing {m}...", end=" ")
        response = client.models.generate_content(model=m, contents="Hi")
        print(f"SUCCESS: {response.text[:20]}...")
    except Exception as e:
        print(f"FAIL: {e}")
