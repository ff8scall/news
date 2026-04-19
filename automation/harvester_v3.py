# -*- coding: utf-8 -*-
import os
import time
import requests
import json
import re
import feedparser
import random
import logging
from datetime import datetime
from common_utils import normalize_url, clean_text, extract_domain
from schemas import HarvestedArticle
from quality_filter import QualityFilter

logger = logging.getLogger("LegoSia.HarvesterV3")

class HarvesterV3:
    """
    [LEGO-SIA V3.0 Strategic Intelligence Harvester]
    - Hybrid Architecture: RSS (Speed/Direct) + API (Diversity)
    - Advanced Deduplication: Persistent URL caching
    - Taxonomy Mapping: Native 8-category support
    - Common Module Integration: standardized cleaning and normalization
    """
    def __init__(self, test_mode=False):
        self.keys = {
            "newsapi": os.getenv("NEWSAPI_ORG_KEY"),
            "gnews": os.getenv("GNEWS_API_KEY")
        }
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(os.path.dirname(current_dir), "docs_private", "rss_feeds.json")
        self.cache_path = os.path.join(current_dir, "cache", "seen_urls.json")
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        
        self.test_mode = test_mode
        self.exhausted = set()
        self.seen_urls = self._load_cache()
        
        self.source_tiers = {
            "tier1": ["Ars Technica", "AnandTech", "Tom's Hardware", "Reuters", "Bloomberg", "TechPowerUp", "ExtremeTech", "IEEE Spectrum"],
            "tier2": ["TechCrunch", "The Verge", "Engadget", "VentureBeat", "Forbes", "Wired", "ZDNet", "ZDNET"],
            "tier3": ["9to5Mac", "Gizmodo", "TNW", "How-To Geek", "ZDNet", "Eurogamer", "IGN", "PC Gamer"]
        }

        self.categories_config = {
            "models": {"kor_name": "AI 모델"},
            "apps": {"kor_name": "AI 활용"},
            "chips": {"kor_name": "반도체"},
            "high-end": {"kor_name": "하이엔드 PC"},
            "analysis": {"kor_name": "비교·분석"},
            "guide": {"kor_name": "개발·팁"}
        }

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def _save_cache(self):
        try:
            # Keep only last 5000 URLs to prevent file bloat
            list_cache = list(self.seen_urls)[-5000:]
            with open(self.cache_path, "w", encoding='utf-8') as f:
                json.dump(list_cache, f)
        except Exception as e:
            logger.error(f" [!] Cache Save Fail: {e}")

    def _get_source_weight(self, source_name):
        if not source_name: return 0.6
        name_l = source_name.lower()
        if any(s.lower() in name_l for s in self.source_tiers["tier1"]): return 1.0
        if any(s.lower() in name_l for s in self.source_tiers["tier2"]): return 0.8
        return 0.6

    def _extract_image(self, entry):
        """RSS 피드에서 가용한 최고 품질의 이미지 URL 추출"""
        # 1. Standard media_content
        if "media_content" in entry and entry["media_content"]:
            return entry["media_content"][0].get("url")
        # 2. Enclosures
        if "links" in entry:
            for link in entry["links"]:
                if link.get("rel") == "enclosure" or "image" in link.get("type", ""):
                    return link.get("href")
        # 3. Content-based extraction (img tag)
        content = entry.get("summary", "") + entry.get("content", [{"value": ""}])[0].get("value", "")
        img_match = re.search(r'<img [^>]*src="([^"]+)"', content)
        if img_match:
            return img_match.group(1)
        # 4. Standard keys
        return entry.get("urlToImage") or entry.get("image_url") or entry.get("image")

    def _normalize_item(self, article, source_name, cat_slug):
        raw_url = article.get("url") or article.get("link", "")
        norm_url = normalize_url(raw_url)
        
        if norm_url in self.seen_urls:
            return None
            
        self.seen_urls.add(norm_url)
        
        return HarvestedArticle(
            title=clean_text(article.get("title", "")),
            description=clean_text(article.get("description", "") or article.get("snippet", ""))[:400],
            url=raw_url,
            normalized_url=norm_url,
            image=self._extract_image(article),
            publishedAt=article.get("publishedAt") or article.get("pubDate") or datetime.now().isoformat(),
            source_name=source_name,
            eng_category_slug=cat_slug,
            source_weight=self._get_source_weight(source_name)
        )

    def fetch_rss(self):
        """
        Directly fetch from high-authority RSS feeds (Tier 1 & 2)
        """
        all_items = []
        if not os.path.exists(self.config_path):
            logger.warning(f" [!] RSS Config Missing: {self.config_path}. Falling back to API-only harvesting.")
            return []

        try:
            with open(self.config_path, "r", encoding='utf-8') as f:
                feeds_config = json.load(f)
            
            for cat_slug, sources in feeds_config.items():
                for source in sources:
                    try:
                        logger.info(f" [*] Fetching RSS: {source['name']} ({cat_slug})")
                        feed = feedparser.parse(source["url"])
                        
                        # Handle Eurogamer etc timeout implicitly by checking if entries exist
                        if not feed.entries:
                            continue
                            
                        for entry in feed.entries[:50]:
                            item = self._normalize_item(entry, source["name"], cat_slug)
                            if item:
                                all_items.append(item)
                    except Exception as e:
                        logger.warning(f" [!] RSS Source Fail ({source['name']}): {e}")
        except Exception as e:
            logger.error(f" [!] RSS Loader Critical Fail: {e}")

        return all_items

    def fetch_all(self, limit_per_cat=3, rss_only=False):
        """
        Main harvesting entry point
        - First gets everything from RSS
        - Then pads with API results if needed
        """
        logger.info(" [>>>] Starting Harvester V3.0 Cycle")
        rss_items = self.fetch_rss()
        
        results = []
        stats = {cat: 0 for cat in self.categories_config}
        
        # Process RSS items first
        for item in rss_items:
            cat = item.eng_category_slug
            if stats[cat] < limit_per_cat * 2: # Allow more from high-quality RSS
                results.append(item)
                stats[cat] += 1
        
        # Save cache after RSS phase
        self._save_cache()
        
        logger.info(f" [+++] RSS Harvest Initial: {len(results)} items found")

        # [V5.0] 2-Pass Quality Filtering
        qf = QualityFilter()
        filtered_results = []
        final_stats = {cat: 0 for cat in self.categories_config}
        
        # 카테고리별로 필터링 실행
        for cat in self.categories_config:
            cat_articles = [a for a in results if a.eng_category_slug == cat]
            if not cat_articles:
                continue
                
            logger.info(f" [FILTER] Processing {cat} ({len(cat_articles)} items)...")
            selected = qf.execute_pipeline(cat_articles, cat, limit=limit_per_cat)
            filtered_results.extend(selected)
            final_stats[cat] = len(selected)

        logger.info(f" [>>>] Filtered Harvest Complete: {len(filtered_results)} high-quality items selected")
        return filtered_results, final_stats

    def dump_to_category_files(self, limit_per_cat=15):
        """
        [V4.0] NotebookLM Macro-Synthesis: Dumps clustered articles to category-specific markdown files.
        Returns a dictionary mapping category to its source file path.
        """
        results, stats = self.fetch_all(limit_per_cat=limit_per_cat)
        
        # Group by category
        grouped = {cat: [] for cat in self.categories_config}
        for item in results:
            cat = item.eng_category_slug
            if cat in grouped:
                grouped[cat].append(item)
                
        output_files = {}
        os.makedirs("scratch", exist_ok=True)
        
        for cat, items in grouped.items():
            if not items:
                continue
            
            filepath = f"scratch/{cat}_raw_dump.md"
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# LEGO-SIA Global Tech Mega-Trend Source Data: {cat}\n")
                    f.write(f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**Total Articles:** {len(items)}\n\n")
                    
                    for idx, a in enumerate(items, 1):
                        tags_str = ", ".join(a.quality_tags) if a.quality_tags else a.eng_category_slug
                        f.write(f"## 📰 [{a.title}]\n")
                        f.write(f"**Meta Info**\n")
                        f.write(f"- **Source:** {a.source_name}\n")
                        f.write(f"- **Date:** {a.publishedAt[:10]}\n")
                        f.write(f"- **URL:** {a.url}\n")
                        f.write(f"- **Quality Score:** {a.quality_score if a.quality_score else 'N/A'}/10\n")
                        f.write(f"- **Tags:** {tags_str}\n\n")
                        
                        desc = a.description.replace('\n', ' ').strip()
                        f.write(f"**본문(Content)**\n{desc}\n\n")
                        f.write("---\n\n")
                
                output_files[cat] = filepath
                logger.info(f" [DUMP] Saved {len(items)} articles to {filepath}")
            except Exception as e:
                logger.error(f" [!] Failed to dump {cat}: {e}")
                
        return output_files

