import os
import requests
import json
from dotenv import load_dotenv

# Load .env
load_dotenv('automation/.env')

GH_MODELS_TOKEN = os.getenv("GH_MODELS_TOKEN")

def test_github_models(model="gpt-4o-mini"):
    print(f"[*] Testing GitHub Models API: {model}")
    url = "https://models.inference.ai.azure.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {GH_MODELS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'GitHub Models are active' in 5 words."}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            result = response.json()
            return f"SUCCESS: {result['choices'][0]['message']['content'].strip()}"
        else:
            return f"FAILED: Status {response.status_code} - {response.text}"
    except Exception as e:
        return f"FAILED: {e}"

if __name__ == "__main__":
    if not GH_MODELS_TOKEN:
        print("Error: Missing GH_MODELS_TOKEN in .env")
    else:
        print(f"Result: {test_github_models()}")
