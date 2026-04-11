import requests
import os
from dotenv import load_dotenv

load_dotenv("automation/.env")
key = os.getenv("NEWSAPI_ORG_KEY")

def test_raw():
    print(f"[*] Testing NewsAPI Raw with Key: {key[:5]}...")
    url = f"https://newsapi.org/v2/everything?q=AI&pageSize=5&apiKey={key}"
    try:
        res = requests.get(url)
        print(f"[*] Status: {res.status_code}")
        data = res.json()
        articles = data.get("articles", [])
        print(f"[*] Found {len(articles)} articles.")
        for a in articles:
            print(f"- Title: {a['title'][:40]}")
            print(f"  Image: {a.get('urlToImage')}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    test_raw()
