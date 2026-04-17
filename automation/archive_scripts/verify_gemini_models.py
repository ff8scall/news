import os
from google import genai
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 테스트할 모델 리스트 (앞서 ListModels로 확인된 후보들)
candidates = [
    "gemini-3.1-flash-lite-preview",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite"
]

working_models = []

print("=== Starting Gemini Model Verification ===")
for model in candidates:
    print(f"[*] Testing {model}...", end=" ", flush=True)
    try:
        response = client.models.generate_content(
            model=model,
            contents="Hello"
        )
        if response and response.text:
            print("SUCCESS [OK]")
            working_models.append(model)
        else:
            print("EMPTY RESPONSE [WARN]")
    except Exception as e:
        print(f"FAILED [FAIL] ({str(e)[:50]})")

print("\n=== Verified Working Models ===")
for wm in working_models:
    print(f"- {wm}")

# 결과를 파일로 저장해 두기 (나중에 참고용)
with open(os.path.join(current_dir, "verified_models.txt"), "w") as f:
    for wm in working_models:
        f.write(wm + "\n")
