import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

class NewsHarvester:
    def __init__(self):
        self.gnews_key = os.getenv("GNEWS_API_KEY")
        self.newsapi_key = os.getenv("NEWSAPI_ORG_KEY")
        self.thenewsapi_key = os.getenv("THENEWSAPI_KEY")
        self.currents_key = os.getenv("CURRENTSAPI_KEY")

    def fetch_all(self, limit_per_api=50):
        print(f"[*] Starting Night-Shift News Harvest (Limit per API: {limit_per_api})...")
        results = []
        
        # 1. GNews (Global Focus) - limit 50 (If plan allows)
        try:
            url = f"https://gnews.io/api/v4/search?q=AI OR NVIDIA OR GPT&lang=en&token={self.gnews_key}&max={limit_per_api}"
            res = requests.get(url, timeout=10).json()
            for i in res.get("articles", []):
                # 이미지 링크 필수 체크
                img = i.get("image") or "https://source.unsplash.com/featured/?ai,tech"
                results.append({"title": i["title"], "url": i["url"], "source": i["source"]["name"], "urlToImage": img})
        except: pass

        # 2. NewsAPI (Technology Focus) - pageSize max (100 is max for free)
        try:
            url = f"https://newsapi.org/v2/everything?q=AI OR Semiconductor&language=en&apiKey={self.newsapi_key}&pageSize={limit_per_api}"
            res = requests.get(url, timeout=10).json()
            for i in res.get("articles", []):
                img = i.get("urlToImage") or "https://source.unsplash.com/featured/?technology"
                results.append({"title": i["title"], "url": i["url"], "source": i["source"]["name"], "urlToImage": img})
        except: pass

        # 3. Currents API
        try:
            url = f"https://api.currentsapi.services/v1/search?apiKey={self.currents_key}&keywords=AI&language=en&limit={limit_per_api}"
            res = requests.get(url, timeout=10).json()
            for i in res.get("news", []):
                img = i.get("image") or "https://source.unsplash.com/featured/?chip,robot"
                results.append({"title": i["title"], "url": i["url"], "source": i["author"], "urlToImage": img})
        except: pass

        seen = set()
        unique = []
        for n in results:
            if n["url"] not in seen:
                unique.append(n)
                seen.add(n["url"])
        
        print(f"[SUCCESS] Night-Shift Harvested {len(unique)} global articles.")
        return unique
