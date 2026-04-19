# -*- coding: utf-8 -*-
"""
[quality_filter.py] Rule-based Resilient Filter (No-API)
======================================================
1. Length-based filtering: Skip shallow content.
2. Keyword-based filtering: Ensure relevance.
3. No external API calls: Avoid throttling and 503/404 errors.
"""

import logging
from typing import List
from schemas import HarvestedArticle, FilterResult

logger = logging.getLogger("LegoSia.QualityFilter")

class QualityFilter:
    def __init__(self, writer=None):
        # We don't need writer/API anymore for filtering
        self.category_keywords = {
            "models": ["AI", "LLM", "GPT", "Gemini", "Claude", "Llama", "transformer", "DeepMind", "OpenAI", "Anthropic", "Mistral", "training", "inference"],
            "apps": ["AI", "copilot", "productivity", "agent", "workflow", "automation", "integration", "software"],
            "chips": ["GPU", "NVIDIA", "AMD", "TSMC", "HBM", "Blackwell", "Intel", "Semiconductor", "Foundry", "wafer", "fab"],
            "high-end": ["9800", "5080", "Snapdragon", "Core Ultra", "Ryzen AI", "AI PC", "Laptop", "Windows 11", "ASUS", "MSI", "Desktop", "Hardware"],
            "analysis": ["Benchmark", "vs", "Comparison", "Review", "Speed test", "Efficiency", "Analysis", "Performance"],
            "guide": ["How to", "Guide", "Tutorial", "Step by step", "Setup", "Install", "Tips", "Tricks", "Best", "Dev"]
        }
        self.blacklist_keywords = ["rumor", "leak", "unconfirmed", "sale", "deal", "discount", "giveaway"]

    def execute_pipeline(self, raw_articles: List[HarvestedArticle], category: str, limit: int = 15) -> List[HarvestedArticle]:
        """
        Rule-based filtering only.
        Selection based on: Length > Relevance > Source Weight.
        """
        result_meta = FilterResult(total_input=len(raw_articles))
        survived = []

        for a in raw_articles:
            text = (a.title + " " + a.description).lower()
            
            # 1. Blacklist Check
            if any(blk in text for blk in self.blacklist_keywords):
                continue
                
            # 2. Length Check (At least 150 chars in description for depth)
            if len(a.description) < 150:
                logger.debug(f" [SKIP] Content too short: {a.title[:30]}...")
                continue
            
            # 3. Keyword/Source Weight Check
            keywords = self.category_keywords.get(category, [])
            matched_kw = [kw for kw in keywords if kw.lower() in text]
            
            if matched_kw or a.source_weight >= 0.8:
                survived.append(a)
                if matched_kw:
                    a.quality_tags.append(f"kw:{matched_kw[0]}")

        # Sort by relevance (Matched Keywords count) and Source Weight
        survived.sort(key=lambda x: (len(x.quality_tags), x.source_weight), reverse=True)
        
        final = survived[:limit]
        
        result_meta.pass1_survived = len(survived)
        result_meta.pass2_selected = len(final)
        result_meta.model_used = "Rule-Based (Length+Relevance)"
        
        logger.info(result_meta.summary())
        return final
