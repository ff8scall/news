import os
import requests
from dotenv import load_dotenv

load_dotenv('automation/.env')

AID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
TOK = os.getenv('CLOUDFLARE_API_TOKEN')

def test_cloudflare(model="@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"):
    print(f"[*] Testing Cloudflare AI: {model}")
    url = f"https://api.cloudflare.com/client/v4/accounts/{AID}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {TOK}"}
    
    try:
        res = requests.post(url, headers=headers, json={"messages": [{"role": "user", "content": "hi"}]})
        if res.status_code == 200:
            return "SUCCESS"
        else:
            return f"FAILED: {res.status_code} - {res.text}"
    except Exception as e:
        return f"FAILED: {e}"

if __name__ == "__main__":
    print(f"Result: {test_cloudflare()}")
