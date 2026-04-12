import os
import sys
import time
import requests
import json
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

# [V13.0 Unchained Net] 인코딩 및 환경 설정
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

class NewsHarvester:
    def __init__(self, test_mode=False):
        self.whitelist_path = os.path.join(os.path.dirname(__file__), '..', 'docs_private', 'rss_feeds.json')
        self.keys = {
            "gnews": os.getenv("GNEWS_API_KEY"),
            "newsapi": os.getenv("NEWSAPI_ORG_KEY"),
            "thenewsapi": os.getenv("THENEWSAPI_KEY"),
            "currents": os.getenv("CURRENTSAPI_KEY"),
            "newsdata": os.getenv("NEWSDATA_API_KEY")
        }
        # [V12.2] API별 한도 및 안전 마진 설정
        self.limits = {
            "gnews": 10, "newsapi": 100, "thenewsapi": 300, 
            "currents": 600, "newsdata": 200
        }
        self.safety_margin = 0.05 
        self.test_mode = test_mode
        self.exhausted = set() 
        
        # [V12.0 Strategic] 전문 키워드 풀
        self.keyword_pools = {
            "ai_tech": ["Multimodal LLM architecture", "Mixture of Experts MoE efficiency", "Neural architecture search", "On-device AI inference", "Quantum machine learning algorithms", "Liquid Neural Networks", "Transformer alternatives (Mamba, RWKV)", "Synthetic data generation"],
            "ai_agent": ["Agentic workflows enterprise", "Autonomous AI planning", "Multi-agent system orchestration", "Self-evolving AI software", "Actionable AI task automation", "AI persona consistency"],
            "hardware": ["Advanced Packaging CoWoS", "High Bandwidth Memory HBM4", "2nm GAA process roadmap", "Custom AI Silicon ASIC", "Photonic interconnects", "Neuromorphic hardware efficiency", "Thermal management AI data center", "Edge computing SoC"],
            "game": ["Unreal Engine 5.5 Nanite tech", "AI generated procedural content", "Neural rendering path tracing", "Micro-transaction AI economy", "Handheld gaming PC innovation", "VR AR spatial computing"],
            "monetization": ["AI SaaS monetization strategy", "LLM unit economics optimization", "Digital advertising AI pivot", "B2B AI adoption ROI", "Subscription fatigue tech solutions"],
            "tech_biz": ["Global semiconductor trade policy", "Big tech antitrust regulation 2026", "AI sovereignty and nation state", "Tech IPO market analysis", "Venture Capital dry powder AI", "Strategic M&A in tech sector"]
        }

        self.categories_config = {
            "ai_tech": {"base_q": "AI technology innovation", "kor_name": "AI Insight", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "ai_agent": {"base_q": "AI Agent automation", "kor_name": "AI Agents", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "hardware": {"base_q": "Next-gen computing hardware", "kor_name": "Computing HW", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "game": {"base_q": "Future of gaming industry", "kor_name": "Next-Gen Game", "thenews_cat": "entertainment", "currents_cat": "arts_culture_entertainment", "newsdata_cat": "entertainment"},
            "business": {"base_q": "Tech business strategy", "kor_name": "Strategy & Biz", "thenews_cat": "business", "currents_cat": "economy_business_finance", "newsdata_cat": "business"},
            "tech_biz": {"base_q": "Global tech market policy", "kor_name": "Market Trend", "thenews_cat": "business", "currents_cat": "economy_business_finance", "newsdata_cat": "business"}
        }

    def _is_safe(self, api_name, res):
        if not res or res.status_code != 200: return False
        headers = res.headers
        rem = headers.get('X-Remaining-Quota') or headers.get('X-RateLimit-Remaining')
        if not rem: return True
        try:
            current_remaining = int(rem)
            limit = self.limits.get(api_name.lower(), 100)
            if current_remaining <= (limit * self.safety_margin):
                print(f" [!] Quota Alert: {api_name} below 5% ({current_remaining}/{limit}). Skipping further calls.")
                self.exhausted.add(api_name.lower())
                return False
        except: pass
        return True

    def _get_dynamic_query(self, cat_key):
        import random
        config = self.categories_config.get(cat_key, {})
        base_q = config.get("base_q", "technology")
        pool = self.keyword_pools.get(cat_key, [])
        sub_q = random.choice(pool) if pool else ""
        return f"{base_q} {sub_q}".strip()

    def _get_time_params(self):
        now = datetime.now()
        if 5 <= now.hour <= 7:
            return "popularity", (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        return "publishedAt", (now - timedelta(minutes=135)).strftime('%Y-%m-%dT%H:%M:%S')

    def _normalize(self, raw, source_api, kor_name):
        title = raw.get("title") or "Untitled Article"
        # [V12.1] 공격적인 이미지 필드 매핑 확장
        image = raw.get("urlToImage") or raw.get("image") or raw.get("image_url") or \
                raw.get("url_to_image") or raw.get("thumbnail") or raw.get("thumbnail_url") or \
                raw.get("media") or raw.get("image_link") or ""
        
        desc = raw.get("description") or raw.get("snippet") or raw.get("content", "")
        url = raw.get("url") or raw.get("link") or ""
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

    def _fetch_newsdata(self, query, kor_name, newsdata_cat, limit):
        # [V12.2] Newsdata.io 신규 엔진 (image=1로 양질의 이미지 기사 우선 수급)
        if "newsdata" in self.exhausted: return []
        url = f"https://newsdata.io/api/1/latest?apikey={self.keys['newsdata']}&q={query}&language=en&category={newsdata_cat}&image=1&size={limit}"
        try:
            res = requests.get(url, timeout=15)
            # Newsdata는 헤더 방식이 다를 수 있어 단순 호출 성공 체크
            if res.status_code == 200:
                data = res.json()
                return [self._normalize(a, "NewsData", kor_name) for a in data.get("results", [])]
            elif res.status_code == 429:
                self.exhausted.add("newsdata")
        except: pass
        return []

    def _categorize_article(self, title, desc):
        # [V13.0] 키워드 기반 지능형 카테고리 매핑
        text = f"{title} {desc}".lower()
        if any(k in text for k in ["ai", "llm", "gpt", "neural", "agent", "deep learning"]): 
            if "agent" in text: return "AI Agents"
            return "AI Insight"
        if any(k in text for k in ["gpu", "processor", "chip", "semiconductor", "hbm", "hw", "hardware"]): return "Computing HW"
        if any(k in text for k in ["game", "gaming", "unreal", "unity", "nintendo", "xbox", "ps5"]): return "Next-Gen Game"
        if any(k in text for k in ["business", "startup", "vc", "founder", "ipo", "monetization"]): return "Strategy & Biz"
        return "Market Trend"

    def _fetch_rss_v13(self):
        # [V13.0] 화이트리스트 기반 광역 RSS 수집
        articles = []
        try:
            if not os.path.exists(self.whitelist_path): return []
            with open(self.whitelist_path, "r") as f:
                whitelist = json.load(f)
            
            for category, sources in whitelist.items():
                for source in sources:
                    try:
                        feed = feedparser.parse(source["url"])
                        for entry in feed.entries[:8]: # 소스당 8개 최신 기사
                            img = None
                            if 'links' in entry:
                                for link in entry.links:
                                    if 'image' in link.get('type', ''): img = link.href
                            
                            # 데이터 정규화 및 자동 카테고리 분류
                            kat = self._categorize_article(entry.title, entry.get('summary', ''))
                            articles.append(self._normalize({
                                "title": entry.title,
                                "description": entry.get('summary', ''),
                                "url": entry.link,
                                "urlToImage": img
                            }, source["name"], kat))
                    except: pass
        except Exception as e:
            print(f" [!] RSS V13 Error: {e}")
        return articles

    def _fetch_kr_rss(self):
        rss_url = "https://www.itworld.co.kr/rss/feed/index.php"
        articles = []
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
                articles.append(self._normalize({"title": entry.title, "description": entry.get('summary', ''), "url": entry.link, "urlToImage": None}, "ITWorld-KR", "테크-비즈니스"))
        except: pass
        return articles

    def fetch_all(self, limit_per_cat=8, rss_only=False):
        all_unique_news = []
        seen_urls = set()
        seen_titles = set() # [V13.0] 제목 기반 중복 제거용
        stats = {"NewsAPI": 0, "TheNewsAPI": 0, "GNews": 0, "Currents": 0, "NewsData": 0, "KR-RSS": 0, "RSS-V13": 0}
        
        print(f"[*] Starting Intelligent Hybrid Harvest (V13.0: RSS-First)...")
        if rss_only: print("[!] RSS-ONLY MODE ACTIVATED. Skipping API Snipering.")
        
        # [STEP 1] RSS 그물망 수집 (The Net)
        print("[*] Stage 1: Harvesting from Global RSS Whitelist...")
        rss_pool = self._fetch_rss_v13()
        stats["RSS-V13"] = len(rss_pool)
        
        # [STEP 2] 카테고 별 기사 풀 생성 (준비)
        category_pools = {k["kor_name"]: [] for k in self.categories_config.values()}
        
        # RSS 기사들을 카테고리별로 분류 및 중복 제거
        for art in rss_pool:
            title_norm = "".join(art["title"].lower().split()) # 공백 제거 정규화
            if title_norm not in seen_titles and art["url"] not in seen_urls:
                cat = art.get("category", "테크-비즈니스")
                if cat in category_pools:
                    category_pools[cat].append(art)
                    seen_titles.add(title_norm)
                    seen_urls.add(art["url"])

        # [STEP 3] 부족한 카메고리만 API 저격총(Sniper) 동원
        strategy_map = {
            "ai_tech": ["NewsAPI", "NewsData", "TheNewsAPI", "GNews", "Currents"],
            "ai_agent": ["NewsAPI", "NewsData", "TheNewsAPI", "Currents", "GNews"],
            "hardware": ["NewsAPI", "GNews", "NewsData", "TheNewsAPI", "Currents"],
            "game": ["GNews", "NewsData", "Currents", "TheNewsAPI", "NewsAPI"],
            "business": ["TheNewsAPI", "NewsData", "Currents", "NewsAPI", "GNews"],
            "tech_biz": ["TheNewsAPI", "NewsData", "Currents", "NewsAPI", "GNews"]
        }

        for internal_key, config in self.categories_config.items():
            kor_name = config["kor_name"]
            current_count = len(category_pools[kor_name])
            
            # 기사가 부족할 때만 API 호출 (쿼터 절약)
            if not rss_only and current_count < (limit_per_cat // 2):
                print(f"[*] Stage 2: Snipering for {kor_name} (Current: {current_count})")
                query = self._get_dynamic_query(internal_key)
                nd_cat = config.get("newsdata_cat", "technology")
                thenews_cat = config.get("thenews_cat", "tech")
                cur_cat = config.get("currents_cat", "general")
                
                priorities = strategy_map.get(internal_key, ["NewsAPI", "NewsData"])
                for api_name in priorities:
                    if api_name.lower() in self.exhausted: continue
                    try:
                        res = []
                        if api_name == "NewsAPI": res = self._fetch_newsapi(query, kor_name, limit_per_cat)
                        elif api_name == "TheNewsAPI": res = self._fetch_thenewsapi(query, kor_name, thenews_cat, limit_per_cat)
                        elif api_name == "GNews": res = self._fetch_gnews(query, kor_name, limit_per_cat)
                        elif api_name == "Currents": res = self._fetch_currents(query, kor_name, cur_cat, limit_per_cat)
                        elif api_name == "NewsData": res = self._fetch_newsdata(query, kor_name, nd_cat, limit_per_cat)

                        if res:
                            stats[api_name] += len(res)
                            for art in res:
                                t_norm = "".join(art["title"].lower().split())
                                if t_norm not in seen_titles and art["url"] not in seen_urls:
                                    category_pools[kor_name].append(art)
                                    seen_titles.add(t_norm)
                                    seen_urls.add(art["url"])
                            
                            if len(category_pools[kor_name]) >= limit_per_cat:
                                break
                        time.sleep(1)
                    except: pass
            
            # 최종 결과 리스트에 병합
            all_unique_news.extend(category_pools[kor_name][:limit_per_cat])
            print(f"    [V] {kor_name} stage: Final size {len(category_pools[kor_name][:limit_per_cat])}")

        # 한국 RSS 추가 (보너스)
        kr_res = self._fetch_kr_rss()
        for art in (kr_res or []):
            t_norm = "".join(art["title"].lower().split())
            if t_norm not in seen_titles and art["url"] not in seen_urls:
                all_unique_news.append(art)
                seen_titles.add(t_norm)
                seen_urls.add(art["url"])
                stats["KR-RSS"] += 1
        
        print(f"[*] Final Intelligence Pool: {len(all_unique_news)} candidates.")
        return all_unique_news, stats
