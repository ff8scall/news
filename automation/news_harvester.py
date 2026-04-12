# -*- coding: utf-8 -*-
import os
import time
import requests
import json
import re
import feedparser
import random
from datetime import datetime

class NewsHarvester:
    """
    [LEGO-SIA V2.0 Strategic Intelligence Harvester]
    - Hybrid 2-Step: RSS (The Net) + API (The Sniper)
    - 12 Strategic Categories
    - Source Tiering & Editorial Scoring
    - Token Pre-Reduction (Sentence Extraction)
    """
    def __init__(self, test_mode=False):
        self.keys = {
            "newsapi": os.getenv("NEWSAPI_ORG_KEY"),
            "thenews": os.getenv("THENEWSAPI_KEY"),
            "currents": os.getenv("CURRENTSAPI_KEY"),
            "gnews": os.getenv("GNEWS_API_KEY"),
            "newsdata": os.getenv("NEWSDATA_API_KEY")
        }
        # [V3.0] 절대 경로 기반 설정 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.whitelist_path = os.path.join(os.path.dirname(current_dir), "docs_private", "rss_feeds.json")
        
        self.test_mode = test_mode
        self.exhausted = set() 
        
        # [V2.0] 수집 소수 신뢰도 등급 (Source Tiering)
        self.source_tiers = {
            "tier1": ["Ars Technica", "AnandTech", "Tom's Hardware", "Reuters", "Bloomberg", "TechPowerUp", "ExtremeTech"],
            "tier2": ["TechCrunch", "The Verge", "Engadget", "VentureBeat", "Forbes", "Fortune", "Wired"],
            "tier3": ["9to5Mac", "Gizmodo", "TNW", "ITWorld-KR", "ETNews-KR"]
        }
        
        # [V2.0 Strategic] 12개 전문 분야로 확장된 키워드 풀
        self.keyword_pools = {
            "llm-tech": ["Large Language Model architecture", "Transformer MoE efficiency", "Reasoning models", "Context window expansion", "Synthetic data training"],
            "ai-agent": ["Agentic workflows", "Autonomous planning", "Multi-agent orchestration", "Tool-use AI", "Self-evolving agents"],
            "ai-policy": ["AI regulation EU Act", "Big tech antitrust AI", "AI safety guidelines", "Ethics in machine learning"],
            "future-sw": ["AI-driven coding", "Natural language programming", "Generative UI UX", "SaaS AI integration"],
            "semi-hbm": ["HBM4 roadmap", "NVIDIA Blackwell specs", "2nm GAA process", "Custom AI ASIC", "Advanced Packaging CoWoS"],
            "hpc-infra": ["AI supercomputer", "Liquid cooling data center", "Photonics interconnect", "Hyperscale infrastructure"],
            "robotics": ["Humanoid robot AI", "End-to-end robotics learning", "Industrial automation 4.0", "Edge AI robotics"],
            "monetization": ["AI SaaS revenue models", "LLM unit economics", "Digital ad AI pivot", "Tech IPO analysis"],
            "startups-vc": ["AI startup funding trends", "Silicon Valley VC dry powder", "Strategic M&A tech sector"],
            "market-trend": ["Semiconductor trade war", "Big tech earnings analysis", "Global tech policy", "Digital sovereignty"],
            "game-tech": ["Unreal Engine 5 Nanite", "Neural rendering", "AI NPC procedural", "Handheld gaming innovation"],
            "spatial-tech": ["Vision Pro spatial computing", "XR industrial use-cases", "MR hardware optics", "Metaverse pivot"]
        }

        self.categories_config = {
            "llm-tech": {"kor_name": "LLM & 모델링", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "ai-agent": {"kor_name": "자율 에이전트", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "ai-policy": {"kor_name": "글로벌 규제·정책", "thenews_cat": "tech", "currents_cat": "politics", "newsdata_cat": "politics"},
            "future-sw": {"kor_name": "지능형 소프트웨어", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "semi-hbm": {"kor_name": "반도체 & 메모리", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "hpc-infra": {"kor_name": "고성능 컴퓨팅(HPC)", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "robotics": {"kor_name": "로봇 & 자동화", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"},
            "monetization": {"kor_name": "성능 전략 & 수익화", "thenews_cat": "business", "currents_cat": "economy_business_finance", "newsdata_cat": "business"},
            "startups-vc": {"kor_name": "스타트업 & 투자", "thenews_cat": "business", "currents_cat": "economy_business_finance", "newsdata_cat": "business"},
            "market-trend": {"kor_name": "글로벌 경제·동향", "thenews_cat": "business", "currents_cat": "economy_business_finance", "newsdata_cat": "business"},
            "game-tech": {"kor_name": "게임 테크", "thenews_cat": "entertainment", "currents_cat": "arts_culture_entertainment", "newsdata_cat": "entertainment"},
            "spatial-tech": {"kor_name": "공간 컴퓨팅", "thenews_cat": "tech", "currents_cat": "science_technology", "newsdata_cat": "technology"}
        }

    def _get_source_weight(self, source_name):
        if not source_name: return 0.6
        name_l = source_name.lower()
        if any(s.lower() in name_l for s in self.source_tiers["tier1"]): return 1.0
        if any(s.lower() in name_l for s in self.source_tiers["tier2"]): return 0.8
        return 0.6

    def _is_safe(self, api_name, res):
        if not res or res.status_code != 200: return False
        rem = res.headers.get('X-Remaining-Quota') or res.headers.get('X-RateLimit-Remaining')
        if rem and str(rem).isdigit() and int(rem) < 10:
            print(f" [!] {api_name} quota exhausted. Skipping.")
            self.exhausted.add(api_name)
            return False
        return True

    def _normalize(self, article, source_name, cat_kor):
        return {
            "title": article.get("title", ""),
            "description": article.get("description", "") or article.get("snippet", ""),
            "content": article.get("content", ""),
            "url": article.get("url", "") or article.get("link", ""),
            "image": article.get("urlToImage") or article.get("image_url") or article.get("image"),
            "publishedAt": article.get("publishedAt") or article.get("pubDate") or datetime.now().isoformat(),
            "source_name": source_name,
            "category_kor": cat_kor
        }

    def _get_dynamic_query(self, cat_key):
        pool = self.keyword_pools.get(cat_key, ["Technology"])
        # [V3.0.20] 매 요청마다 키워드 순서를 섞어 다양성 확보
        shuffled = pool.copy()
        random.shuffle(shuffled)
        return shuffled[0]

    def _categorize_article(self, title, description):
        text = f"{title} {description}".lower()
        
        # [V2.0 Priority Rule] Hardware/Gaming keywords override others
        hw_keywords = ["gpu", "nvidia", "hbm", "semiconductor", "tsmc", "foundry", "chip", "processor", "memory", "intel", "amd", "server", "data center", "robot", "humanoid", "automation"]
        game_keywords = ["unreal engine", "game engine", "ps5", "xbox", "nintendo", "benchmark", "fps", "rtx", "graphics"]
        
        if any(k in text for k in hw_keywords):
            if any(k in text for k in ["robot", "humanoid", "automation"]): return "robotics"
            if any(k in text for k in ["server", "data center", "hpc"]): return "hpc-infra"
            return "semi-hbm"
        
        if any(k in text for k in game_keywords): return "game-tech"
        
        # Strategic/Money priority
        money_keywords = ["saas", "subscription", "revenue", "ipo", "funding", "vc ", "investment", "m&a", "startup", "economy", "market"]
        if any(k in text for k in money_keywords):
            if any(k in text for k in ["funding", "vc ", "investment", "startup"]): return "startups-vc"
            if any(k in text for k in ["revenue", "saas", "pricing"]): return "monetization"
            return "market-trend"
        
        # AI/Software priority (More Granular)
        if any(k in text for k in ["agent", "autonomous", "planning", "tool-use", "reasoning"]): return "ai-agent"
        if any(k in text for k in ["policy", "regulation", "law", "antitrust", "ethics", "guideline"]): return "ai-policy"
        if any(k in text for k in ["llm", "gpt", "transformer", "diffusion", "rag ", "vector", "inference", "fine-tune"]): return "llm-tech"
        
        return "future-sw"

    def extract_core_sentences(self, content):
        """[V2.0] Token Pre-Reduction Engine: 핵심 5문장 추출"""
        if not content or len(content) < 200: return content
        
        sentences = re.split(r'(?<=[.!?])\s+', content)
        scored_sentences = []
        
        for s in sentences:
            score = 0
            if re.search(r'\d+', s): score += 3 # 숫자 포함
            if any(k in s.lower() for k in ["$ ", "percent", "launch", "announced", "spec", "performance", "bench", "vs"]): score += 2
            if len(s) > 30 and len(s) < 200: score += 1
            scored_sentences.append((score, s))
        
        top_indices = sorted(range(len(scored_sentences)), key=lambda i: scored_sentences[i][0], reverse=True)[:5]
        selected = [sentences[i] for i in sorted(top_indices)]
        return " ".join(selected)

    def fetch_all(self, limit_per_cat=8, rss_only=False, target_cats=None):
        results = []
        stats = {cat: 0 for cat in self.categories_config}
        
        # 1. RSS 처리 (Tier 시스템 적용 및 카테고리별 수량 캡핑)
        rss_data = self._fetch_rss_v13()
        print(f" [*] RSS Harvested: {len(rss_data)} items")
        for item in rss_data:
            cat = self._categorize_article(item['title'], item['description'])
            
            # [V3.0.26] 수량 캡핑: 특정 범주(건수가 많은 future-sw 등)가 리포트를 독점하지 않도록 최대 20건으로 제한
            if stats[cat] >= 20: continue
            
            item['eng_category_slug'] = cat
            item['source_weight'] = self._get_source_weight(item.get('source_name', 'Unknown'))
            item['content_summary'] = self.extract_core_sentences(item.get('description', ''))
            results.append(item)
            stats[cat] += 1
            
        if rss_only: return results, stats

        # 2. Sniper API 처리 (수량 미달 카테코리 보충)
        # [V3.0.20] 카테고리 순서를 섞어 전체적으로 고른 수확 보장
        cats_to_snipe = list(target_cats if target_cats else self.categories_config.keys())
        random.shuffle(cats_to_snipe)
        
        for cat_key in cats_to_snipe:
            if cat_key not in self.categories_config: continue
            if stats[cat_key] >= limit_per_cat: continue
            
            config = self.categories_config[cat_key]
            needed = limit_per_cat - stats[cat_key]
            query = self._get_dynamic_query(cat_key)
            print(f" [*] Sniping: {cat_key} -> Query: {query} (Need: {needed})")
            
            # NewsAPI as primary sniper
            if "newsapi" not in self.exhausted:
                api_results = self._fetch_newsapi(query, config['kor_name'], needed)
                for item in api_results:
                    item['eng_category_slug'] = cat_key
                    item['source_weight'] = self._get_source_weight(item.get('source_name', 'Unknown'))
                    item['content_summary'] = self.extract_core_sentences(item.get('description', ''))
                    results.append(item)
                    stats[cat_key] += 1
                    
        return results, stats

    def _fetch_newsapi(self, query, kor_name, limit):
        if not self.keys['newsapi'] or "newsapi" in self.exhausted: return []
        
        # [V3.0.20] Adaptive Time Window: 신선도가 최우선이나 발견되지 않을 경우 범위 확장
        # 기본 24시간 -> 결과 없을 시 7일(fallback)
        time_windows = [
            datetime.now().strftime('%Y-%m-%dT00:00:00'),
            (datetime.now().strftime('%Y-%m-%d')) # Today
        ]
        
        page_size = max(10, min(limit * 3, 20))
        
        for from_date in time_windows:
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&language=en&pageSize={page_size}&apiKey={self.keys['newsapi']}"
            try:
                res = requests.get(url, timeout=12)
                if self._is_safe("newsapi", res):
                    data = res.json()
                    articles = data.get("articles", [])
                    if articles:
                        return [self._normalize(a, a.get("source", {}).get("name", "NewsAPI"), kor_name) for a in articles]
            except: pass
        
        # [Final Fallback] 전체 기간 검색 (결과 매우 부족시)
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&language=en&pageSize={page_size}&apiKey={self.keys['newsapi']}"
        try:
            res = requests.get(url, timeout=12)
            if self._is_safe("newsapi", res):
                data = res.json()
                return [self._normalize(a, a.get("source", {}).get("name", "NewsAPI"), kor_name) for a in data.get("articles", [])]
        except: pass
        return []

    def _fetch_rss_v13(self):
        articles = []
        try:
            if not os.path.exists(self.whitelist_path): return []
            with open(self.whitelist_path, "r") as f:
                whitelist = json.load(f)
            
            for category, sources in whitelist.items():
                for source in sources:
                    try:
                        feed = feedparser.parse(source["url"])
                        for entry in feed.entries[:8]:
                            img = None
                            # 1. Look for media:content (Standard)
                            if 'media_content' in entry and len(entry.media_content) > 0:
                                img = entry.media_content[0].get('url')
                            
                            # 2. Look for media:thumbnail
                            if not img and 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                                img = entry.media_thumbnail[0].get('url')
                            
                            # 3. Look for enclosure (common for images)
                            if not img and 'enclosures' in entry:
                                for encl in entry.enclosures:
                                    if encl.get('type', '').startswith('image/'):
                                        img = encl.get('url')
                            
                            # 4. Look for links with image type
                            if not img and 'links' in entry:
                                for link in entry.links:
                                    if 'image' in link.get('type', ''): img = link.get('href')
                            
                            # 5. [V3.0.35] Content/Summary HTML Parsing Fallback
                            if not img:
                                html_search_targets = []
                                if 'content' in entry: html_search_targets.append(entry.content[0].value)
                                if 'summary' in entry: html_search_targets.append(entry.summary)
                                
                                for html in html_search_targets:
                                    img_match = re.search(r'<img [^>]*src="([^"]+)"', html)
                                    if img_match:
                                        img = img_match.group(1)
                                        break

                            articles.append({
                                "title": entry.title,
                                "description": entry.get('summary', ''),
                                "url": entry.link,
                                "image": img,
                                "source_name": source["name"]
                            })
                    except: pass
        except Exception as e:
            print(f" [!] RSS V13 Error: {e}")
        return articles
