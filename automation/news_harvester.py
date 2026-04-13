# -*- coding: utf-8 -*-
import os
import time
import requests
import json
import re
import feedparser
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("LegoSia.Harvester")

class NewsHarvester:
    """
    [LEGO-SIA V2.2 Professional Intelligence Harvester]
    - Hybrid 2-Step: RSS (The Net) + API (The Sniper)
    - Source Tiering & Image Extraction
    - [V0.2.2] Edge-case Logging & Robust Duplicate Filtering
    """
    def __init__(self, test_mode=False):
        self.keys = {
            "newsapi": os.getenv("NEWSAPI_ORG_KEY"),
            "gnews": os.getenv("GNEWS_API_KEY")
        }
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.whitelist_path = os.path.join(os.path.dirname(current_dir), "docs_private", "rss_feeds.json")
        
        self.test_mode = test_mode
        self.exhausted = set() 
        
        self.source_tiers = {
            "tier1": ["Ars Technica", "AnandTech", "Tom's Hardware", "Reuters", "Bloomberg", "TechPowerUp", "ExtremeTech"],
            "tier2": ["TechCrunch", "The Verge", "Engadget", "VentureBeat", "Forbes", "Fortune", "Wired"],
            "tier3": ["9to5Mac", "Gizmodo", "TNW", "ITWorld-KR", "ETNews-KR"]
        }
        
        self.keyword_pools = {
            "ai-models": ["ChatGPT gpt-5", "Claude 3.5", "Gemini 1.5 Pro", "Llama 3 open source"],
            "ai-tools": ["Cursor AI editor", "GitHub Copilot", "Midjourney", "v0 dev"],
            "gpu-chips": ["NVIDIA Blackwell", "RTX 5090 specs", "HBM3E", "TSMC 2nm", "AMD Instinct"],
            "pc-robotics": ["AI Workstation", "Tesla Optimus", "Humanoid AI", "Figure AI"],
            "game-optimization": ["Unreal Engine 5.5", "DLSS 4.0", "Game performance optimization"],
            "ai-gameplay": ["AI NPC interaction", "Procedural game AI", "Generative AI gaming"],
            "tutorials": ["AI tool tutorial", "Step by step AI guide", "How to use local LLM"],
            "compare": ["AI model comparison", "RTX 5090 vs 4090", "Claude vs ChatGPT benchmark"]
        }

        self.categories_config = {
            "ai-models": {"kor_name": "AI 모델·트렌드"},
            "ai-tools": {"kor_name": "AI 도구·사용법"},
            "gpu-chips": {"kor_name": "GPU·반도체"},
            "pc-robotics": {"kor_name": "AI PC·로봇"},
            "game-optimization": {"kor_name": "게임 최적화·엔진"},
            "ai-gameplay": {"kor_name": "AI 게임 기술"},
            "tutorials": {"kor_name": "실전 튜토리얼"},
            "compare": {"kor_name": "성능 비교"}
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
            logger.warning(f" [!] {api_name} quota exhausted.")
            self.exhausted.add(api_name)
            return False
        return True

    def _normalize(self, article, source_name, cat_kor):
        # [V0.2.2 Fix] Essential Hugo Quote Escaping
        title = article.get("title", "").replace('"', "'")
        desc = (article.get("description", "") or article.get("snippet", ""))[:200].replace('"', "'")
        return {
            "title": title,
            "description": desc,
            "content": article.get("content", ""),
            "url": article.get("url", "") or article.get("link", ""),
            "image": article.get("urlToImage") or article.get("image_url") or article.get("image"),
            "publishedAt": article.get("publishedAt") or article.get("pubDate") or datetime.now().isoformat(),
            "source_name": source_name,
            "category_kor": cat_kor
        }

    def _categorize_article(self, title, description):
        text = f"{title} {description}".lower()
        # [V0.2.2] Prioritize Guides/Compare
        if any(k in text for k in ["how to", "tutorial", "guide", "setup", "walkthrough", "vs", "compare", "benchmark", "versus"]):
            if any(k in text for k in ["vs", "compare", "benchmark", "versus"]): return "compare"
            return "tutorials"
        if any(k in text for k in ["unreal engine", "dlss", "rtx", "frame rate", "fps", "game engine", "npc"]):
            if any(k in text for k in ["dlss", "optimi", "fps", "performance", "engine"]): return "game-optimization"
            return "ai-gameplay"
        if any(k in text for k in ["nvidia", "hbm", "semi", "gpu", "chip", "intel", "amd", "robot", "humanoid", "pc build"]):
            if any(k in text for k in ["robot", "humanoid", "pc", "workstation"]): return "pc-robotics"
            return "gpu-chips"
        if any(k in text for k in ["cursor", "copilot", "prompt", "use", "tool"]): return "ai-tools"
        return "ai-models"

    def extract_core_sentences(self, content):
        if not content or len(content) < 200: return content
        sentences = re.split(r'(?<=[.!?])\s+', content)
        scored = []
        for s in sentences:
            score = 0
            if re.search(r'\d+', s): score += 3
            if any(k in s.lower() for k in ["launch", "announced", "spec", "performance", "bench", "vs"]): score += 2
            scored.append((score, s))
        top_indices = sorted(range(len(scored)), key=lambda i: scored[i][0], reverse=True)[:5]
        return " ".join([sentences[i] for i in sorted(top_indices)])

    def fetch_all(self, limit_per_cat=8, rss_only=False, target_cats=None):
        results = []; stats = {cat: 0 for cat in self.categories_config}
        rss_data = self._fetch_rss_v13()
        logger.info(f" [*] RSS Harvested: {len(rss_data)} items")
        for item in rss_data:
            cat = self._categorize_article(item['title'], item['description'])
            if stats[cat] >= 20: continue
            item['eng_category_slug'] = cat
            item['source_weight'] = self._get_source_weight(item.get('source_name', 'Unknown'))
            item['content_summary'] = self.extract_core_sentences(item.get('description', ''))
            results.append(item); stats[cat] += 1
            
        if rss_only: return results, stats
        
        cats_to_snipe = list(target_cats if target_cats else self.categories_config.keys())
        random.shuffle(cats_to_snipe)
        for cat_key in cats_to_snipe:
            if stats[cat_key] >= limit_per_cat: continue
            needed = limit_per_cat - stats[cat_key]
            query = self.keyword_pools[cat_key][random.randint(0, len(self.keyword_pools[cat_key])-1)]
            logger.info(f" [*] Sniping: {cat_key} (Need: {needed})")
            
            api_results = []
            if "newsapi" not in self.exhausted: api_results = self._fetch_newsapi(query, self.categories_config[cat_key]['kor_name'], needed)
            if not api_results and "gnews" not in self.exhausted: api_results = self._fetch_gnews(query, self.categories_config[cat_key]['kor_name'], needed)
            
            for item in api_results:
                item['eng_category_slug'] = cat_key
                item['source_weight'] = self._get_source_weight(item.get('source_name', 'Unknown'))
                item['content_summary'] = self.extract_core_sentences(item.get('description', ''))
                if len(item['content_summary']) >= 150:
                    results.append(item); stats[cat_key] += 1
        return results, stats

    def _fetch_rss_v13(self):
        articles = []; seen_urls = set()
        try:
            if not os.path.exists(self.whitelist_path): 
                logger.error(f" [!] RSS Config Missing: {self.whitelist_path}")
                return []
            with open(self.whitelist_path, "r") as f: whitelist = json.load(f)
            
            for category, sources in whitelist.items():
                for source in sources:
                    try:
                        feed = feedparser.parse(source["url"])
                        if feed.get('bozo_exception'):
                            logger.warning(f" [!] Feed Exception ({source['name']}): {feed.bozo_exception}")
                            continue
                        for entry in feed.entries[:8]:
                            url = entry.link
                            if url in seen_urls: continue
                            seen_urls.add(url)
                            img = None
                            if 'media_content' in entry and len(entry.media_content) > 0: img = entry.media_content[0].get('url')
                            if not img and 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0: img = entry.media_thumbnail[0].get('url')
                            if not img:
                                for html in [entry.get('summary', ''), entry.get('content', [{'value': ''}])[0]['value']]:
                                    img_match = re.search(r'<img [^>]*src="([^"]+)"', html)
                                    if img_match: img = img_match.group(1); break
                            articles.append({"title": entry.title, "description": entry.get('summary', ''), "url": url, "image": img, "source_name": source["name"]})
                    except Exception as e:
                        logger.error(f" [!] RSS Source Fail ({source['name']}): {e}")
        except Exception as e:
            logger.error(f" [!] RSS Loader Critical Fail: {e}")
        return articles

    def _fetch_newsapi(self, query, kor_name, limit):
        if not self.keys['newsapi'] or "newsapi" in self.exhausted: return []
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&pageSize={limit*2}&apiKey={self.keys['newsapi']}"
        try:
            res = requests.get(url, timeout=12)
            if self._is_safe("newsapi", res):
                return [self._normalize(a, a.get("source", {}).get("name", "NewsAPI"), kor_name) for a in res.json().get("articles", [])]
        except: pass
        return []

    def _fetch_gnews(self, query, kor_name, limit):
        if not self.keys['gnews'] or "gnews" in self.exhausted: return []
        url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max={limit}&token={self.keys['gnews']}"
        try:
            res = requests.get(url, timeout=12)
            if self._is_safe("gnews", res):
                return [self._normalize(a, a.get("source", {}).get("name", "GNews"), kor_name) for a in res.json().get("articles", [])]
        except: pass
        return []
