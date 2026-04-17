import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Starting Simple Test...")
# Try the ones that worked in the beginning of the turno
models = ["gemini-3.1-flash-lite-preview", "gemini-1.5-flash", "gemini-1.5-pro"]
for m in models:
    print(f"Testing {m}:", end=" ", flush=True)
    try:
        response = client.models.generate_content(model=m, contents="Hello. Response: ", config={'max_output_tokens': 100})
        print(f"SUCCESS -> {response.text}")
    except Exception as e:
        print(f"FAILED -> {e}")
