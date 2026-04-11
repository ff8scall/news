import os
import requests
import time
import sys
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

# [V10.9] 터미널 로깅 최적화
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# .env 로드
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

class NewsHarvester:
    def __init__(self, test_mode=False):
        self.keys = {
            "gnews": os.getenv("GNEWS_API_KEY"),
            "newsapi": os.getenv("NEWSAPI_ORG_KEY"),
            "thenewsapi": os.getenv("THENEWSAPI_KEY"),
            "currents": os.getenv("CURRENTSAPI_KEY")
        }
        # [V10.9] API별 일일 한도 설정 및 15% 안전 마진
        self.limits = {
            "gnews": 10,
            "newsapi": 100,
            "thenewsapi": 300,
            "currents": 600
        }
        self.safety_margin = 0.15 
        self.test_mode = test_mode
        self.exhausted = set() # 기력 소진된 API 목록
        
        # [V12.0 Strategic] 전문 용어 및 비즈니스 임팩트 중심 키워드 풀 확장
        self.keyword_pools = {
            "ai_tech": [
                "Multimodal LLM architecture", "Mixture of Experts MoE efficiency", 
                "Neural architecture search", "On-device AI inference", 
                "Quantum machine learning algorithms", "Liquid Neural Networks",
                "Transformer alternatives (Mamba, RWKV)", "Synthetic data generation"
            ],
            "ai_agent": [
                "Agentic workflows enterprise", "Autonomous AI planning", 
                "Multi-agent system orchestration", "Self-evolving AI software",
                "Actionable AI task automation", "AI persona consistency"
            ],
            "hardware": [
                "Advanced Packaging CoWoS", "High Bandwidth Memory HBM4", 
                "2nm GAA process roadmap", "Custom AI Silicon ASIC", 
                "Photonic interconnects", "Neuromorphic hardware efficiency",
                "Thermal management AI data center", "Edge computing SoC"
            ],
            "game": [
                "Unreal Engine 5.5 Nanite tech", "AI generated procedural content", 
                "Neural rendering path tracing", "Micro-transaction AI economy",
                "Handheld gaming PC innovation", "VR AR spatial computing"
            ],
            "monetization": [
                "AI SaaS monetization strategy", "LLM unit economics optimization", 
                "Digital advertising AI pivot", "B2B AI adoption ROI",
                "Subscription fatigue tech solutions"
            ],
            "tech_biz": [
                "Global semiconductor trade policy", "Big tech antitrust regulation 2026", 
                "AI sovereignty and nation state", "Tech IPO market analysis",
                "Venture Capital dry powder AI", "Strategic M&A in tech sector"
            ]
        }

        self.categories_config = {
            "ai_tech": {"base_q": "AI technology innovation", "kor_name": "AI-기술", "thenews_cat": "tech", "currents_cat": "science_technology"},
            "ai_agent": {"base_q": "AI Agent automation", "kor_name": "AI-에이전트", "thenews_cat": "tech", "currents_cat": "science_technology"},
            "hardware": {"base_q": "Next-gen computing hardware", "kor_name": "하드웨어", "thenews_cat": "tech", "currents_cat": "science_technology"},
            "game": {"base_q": "Future of gaming industry", "kor_name": "게임", "thenews_cat": "entertainment", "currents_cat": "arts_culture_entertainment"},
            "business": {"base_q": "Tech business strategy", "kor_name": "수익화-전략", "thenews_cat": "business", "currents_cat": "economy_business_finance"},
            "tech_biz": {"base_q": "Global tech market policy", "kor_name": "테크-비즈니스", "thenews_cat": "business", "currents_cat": "economy_business_finance"}
        }

    def _is_safe(self, api_name, res):
        """[V10.9] 헤더를 분석하여 15% 잔량 유지 여부 판단"""
        if not res or res.status_code != 200: return False
        headers = res.headers
        rem = headers.get('X-Remaining-Quota') or headers.get('X-RateLimit-Remaining')
        if not rem: return True
        try:
            current_remaining = int(rem)
            limit = self.limits.get(api_name.lower(), 100)
            if current_remaining <= (limit * self.safety_margin):
                print(f" [!] Quota Alert: {api_name} below 15% ({current_remaining}/{limit}). Skipping further calls.")
                self.exhausted.add(api_name.lower())
                return False
        except: pass
        return True

    def _get_dynamic_query(self, cat_key):
        """[V12.0] 전문 키워드 로테이션 및 전략적 쿼리 생성"""
        import random
        config = self.categories_config.get(cat_key, {})
        base_q = config.get("base_q", "technology")
        pool = self.keyword_pools.get(cat_key, [])
        
        # 전문 키워드 1개 선택 + 베이스 쿼리 조합
        sub_q = random.choice(pool) if pool else ""
        return f"{base_q} {sub_q}".strip()

    def _get_time_params(self):
        """[V12.0] 골든 타임 및 속보 윈도우 계산"""
        now = datetime.now()
        # 새벽 5~7시: 글로벌 메가 트렌드 가중치 (popularity)
        if 5 <= now.hour <= 7:
            sort_by = "popularity"
            from_time = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        else:
            sort_by = "publishedAt"
            from_time = (now - timedelta(minutes=135)).strftime('%Y-%m-%dT%H:%M:%S') # 2시간 + 여유분
        
        return sort_by, from_time

    def _normalize(self, raw, source_api, kor_name):
        title = raw.get("title") or "Untitled Article"
        image = raw.get("urlToImage") or raw.get("image") or raw.get("image_url") or ""
        desc = raw.get("description") or raw.get("snippet") or raw.get("content", "")
        url = raw.get("url") or ""
        source = raw.get("source", {}).get("name") if isinstance(raw.get("source"), dict) else raw.get("source", source_api)
        return {"title": title, "description": desc, "urlToImage": image, "url": url, "source": source, "category": kor_name}

    def _fetch_newsapi(self, query, kor_name, limit):

        if "newsapi" in self.exhausted: return []
        sort_by, from_time = self._get_time_params()
        url = f"https://newsapi.org/v2/everything?q={query}&from={from_time}&sortBy={sort_by}&language=en&apiKey={self.keys['newsapi']}&pageSize={limit}"
        try:
            res = requests.get(url, timeout=12)
            if self._is_safe("newsapi", res):
                data = res.json()
                return [self._normalize(a, "NewsAPI", kor_name) for a in data.get("articles", [])]
        except: pass
        return []

    def _fetch_thenewsapi(self, query, kor_name, thenews_cat, limit):
        if "thenewsapi" in self.exhausted: return []
        url = f"https://api.thenewsapi.com/v1/news/all?api_token={self.keys['thenewsapi']}&categories={thenews_cat}&language=en&limit={limit}"
        try:
            res = requests.get(url, timeout=12)
            if self._is_safe("thenewsapi", res):
                data = res.json()
                return [self._normalize(a, "TheNewsAPI", kor_name) for a in data.get("data", [])]
        except: pass
        return []

    def _fetch_gnews(self, query, kor_name, limit):
        if "gnews" in self.exhausted: return []
        # GNews는 검색 쿼리를 단순화해야 결과가 잘 나옴
        short_q = query.split(' ')[0]
        url = f"https://gnews.io/api/v4/search?q={short_q}&lang=en&max={limit}&token={self.keys['gnews']}"
        try:
            res = requests.get(url, timeout=12)
            self._is_safe("gnews", res)
            data = res.json()
            return [self._normalize(a, "GNews", kor_name) for a in data.get("articles", [])]
        except: pass
        return []

    def _fetch_currents(self, query, kor_name, currents_cat, limit):
        if "currents" in self.exhausted: return []
        url = f"https://api.currentsapi.services/v2/latest-news?apiKey={self.keys['currents']}&category={currents_cat}&language=en"
        try:
            res = requests.get(url, timeout=15)
            self._is_safe("currents", res)
            data = res.json()
            return [self._normalize(a, "Currents-V2", kor_name) for a in data.get("news", [])[:limit]]
        except: pass
        return []

    def _fetch_kr_rss(self):
        rss_url = "https://www.itworld.co.kr/rss/feed/index.php"
        articles = []
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
                articles.append(self._normalize({"title": entry.title, "description": entry.get('summary', ''), "url": entry.link, "urlToImage": None}, "ITWorld-KR", "테크-비즈니스"))
        except: pass
        return articles

    def fetch_all(self, limit_per_cat=5):
        all_unique_news = []
        seen_urls = set()
        print(f"[*] Starting Intelligence Harvest (Strategic Mode: 6:2:2)...")
        
        for internal_key, config in self.categories_config.items():
            kor_name = config["kor_name"]
            query = self._get_dynamic_query(internal_key)
            thenews_cat = config.get("thenews_cat", "tech")
            cur_cat = config.get("currents_cat", "general")
            
            print(f"[*] Processing: {kor_name} (Query: {query})")
            cat_results = []
            
            if self.test_mode:
                print(f"    [!] TEST MODE: Harvesting from Currents only")
                cat_results += self._fetch_currents(query, kor_name, cur_cat, limit_per_cat)
            else:
                # [V10.9] API 전체 동원 및 소진 대응
                cat_results += self._fetch_newsapi(query, kor_name, limit_per_cat)
                time.sleep(1)
                cat_results += self._fetch_thenewsapi(query, kor_name, thenews_cat, limit_per_cat)
                time.sleep(1)
                cat_results += self._fetch_gnews(query, kor_name, limit_per_cat)
                time.sleep(1)
                cat_results += self._fetch_currents(query, kor_name, cur_cat, limit_per_cat)
            
            for article in cat_results:
                if article["url"] and article["url"] not in seen_urls:
                    all_unique_news.append(article)
                    seen_urls.add(article["url"])
            
            print(f"    [V] {kor_name} stage: Current pool size {len(all_unique_news)}")
            time.sleep(1)

        # KR RSS는 항상 보너스로 추가
        all_unique_news += self._fetch_kr_rss()
        
        print(f"[*] Final Intelligence Pool: {len(all_unique_news)} candidates.")
        return all_unique_news
