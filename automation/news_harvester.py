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
        # [V3.7] 안정성 강화: 쿼리를 쪼개서 개별적으로 요청 (에러 방지)
        target_keywords = ["NVIDIA", "AI Tech", "RTX 5090", "HBM4", "Nintendo Switch 2", "AI SaaS"]
        print(f"[*] Multi-Query Harvest Level 2...")
        
        results = []
        
        # GNews (가장 안정적)
        for kw in target_keywords[:3]:
            try:
                url = f"https://gnews.io/api/v4/search?q={kw}&lang=en&token={self.gnews_key}&max=10"
                res = requests.get(url, timeout=10).json()
                for i in res.get("articles", []):
                    # 이미지 링크 필수 체크
                    img = i.get("image") or "https://source.unsplash.com/featured/?ai,tech"
                    results.append({
                        "title": i["title"], 
                        "description": i.get("description", ""), # 원본 설명 추가
                        "url": i["url"], 
                        "source": i["source"]["name"], 
                        "urlToImage": img
                    })
            except: pass

        # 2. NewsAPI (Technology Focus)
        try:
            q = " OR ".join(target_keywords[3:]) 
            url = f"https://newsapi.org/v2/everything?q={q}&language=en&apiKey={self.newsapi_key}&pageSize={limit_per_api}"
            res = requests.get(url, timeout=10).json()
            for i in res.get("articles", []):
                img = i.get("urlToImage") or "https://source.unsplash.com/featured/?technology"
                results.append({
                    "title": i["title"], 
                    "description": i.get("description", ""), # 원본 설명 추가
                    "url": i["url"], 
                    "source": i["source"]["name"], 
                    "urlToImage": img
                })
        except: pass

        seen = set()
        unique = []
        for n in results:
            if n["url"] not in seen:
                if not n.get("urlToImage"):
                    n["urlToImage"] = "https://source.unsplash.com/featured/?technology"
                unique.append(n)
                seen.add(n["url"])
        
        print(f"[SUCCESS] Total {len(unique)} candidate articles collected.")
        return unique
