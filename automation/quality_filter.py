# -*- coding: utf-8 -*-
"""
[quality_filter.py] Hybrid LLM-based Quality Scorer
======================================================
1. Blacklist Filtering: Immediate noise removal.
2. Length Check: Skip extremely shallow content.
3. LLM Scorer (Gemini): Batch analysis for high-quality selection.
"""

import os
import re
import json
import logging
import google.generativeai as genai
from typing import List
from schemas import HarvestedArticle, FilterResult
from dotenv import load_dotenv

# Load env for API Key
load_dotenv()

logger = logging.getLogger("LegoSia.QualityFilter")

class QualityFilter:
    def __init__(self, writer=None):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-3-flash-preview')
                logger.info(" [QualityFilter] Gemini 3 Flash Preview initialized for scoring.")
            except Exception as e:
                logger.error(f" [QualityFilter] Failed to init Gemini: {e}")
                self.model = None
        else:
            self.model = None
            logger.warning(" [QualityFilter] GEMINI_API_KEY not found. Falling back to rule-based behavior.")
            
        self.blacklist_keywords = ["rumor", "leak", "unconfirmed", "sale", "deal", "discount", "giveaway", "freebie", "price drop"]

    def _llm_select_batch(self, articles: List[HarvestedArticle], category: str) -> List[int]:
        """
        [V6.0] Batch selection using Gemini 1.5 Flash.
        Sends Titles and Snippets to LLM to get selected indices.
        """
        if not self.model or not articles:
            return list(range(len(articles)))
            
        # 1. Prepare batch text
        items_text = ""
        for i, a in enumerate(articles):
            # Limit snippet length to save tokens
            snippet = a.description[:300] if a.description else "No description available."
            items_text += f"ID: {i}\nTitle: {a.title}\nSnippet: {snippet}\n\n"
            
        category_map = {
            "ai": "Artificial Intelligence & Software Trends",
            "hardware": "Computing Hardware, Semiconductors & Devices",
            "insights": "Industry Analysis, Technical Reviews & Market Insights"
        }
        target_cat = category_map.get(category, category)
            
        prompt = (
            f"You are a professional tech editor. Review the following news items harvested for the '{target_cat}' category.\n"
            "Criteria for selection:\n"
            "1. Deep insights, technical announcements, or significant industry shifts.\n"
            "2. Professional journalism or high-authority technical sources.\n"
            "3. Skip low-quality content, simple price updates, generic lists, or noise.\n\n"
            "--- ITEMS START ---\n"
            f"{items_text}\n"
            "--- ITEMS END ---\n\n"
            "Output the IDs of the selected articles as a JSON list of integers. Example: [0, 2, 5]. "
            "Return ONLY the valid JSON list and nothing else."
        )
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()
            # Extract JSON list using regex
            match = re.search(r"(\[.*?\])", raw_text.replace("\n", ""), re.S)
            if match:
                selected_ids = json.loads(match.group(1))
                # Validate bounds
                valid_ids = [idx for idx in selected_ids if isinstance(idx, int) and 0 <= idx < len(articles)]
                logger.info(f" [LLM] Selected {len(valid_ids)}/{len(articles)} items for {category}.")
                return valid_ids
        except Exception as e:
            logger.error(f" [LLM ERROR] Batch selection failed: {e}")
            
        # Fallback: if error, return all for manual check later (resilience)
        return list(range(len(articles)))

    def execute_pipeline(self, raw_articles: List[HarvestedArticle], category: str, limit: int = 12) -> List[HarvestedArticle]:
        """
        Refined Pipeline: Blacklist -> Length Check -> LLM Selection.
        """
        result_meta = FilterResult(total_input=len(raw_articles))
        
        # Step 1: Pre-filtering (Noise removal)
        pre_filtered = []
        for a in raw_articles:
            text = (a.title + " " + (a.description or "")).lower()
            
            # Blacklist
            if any(blk in text for blk in self.blacklist_keywords):
                continue
                
            # Basic Length check (Loose: 40 chars)
            if len(a.description or "") < 40 and len(a.title) < 50:
                continue
                
            pre_filtered.append(a)
            
        # Step 2: LLM Quality Selection (Option 2)
        if not pre_filtered:
            result_meta.pass1_survived = 0
            result_meta.pass2_selected = 0
            result_meta.model_used = "Rule-Based (Empty)"
            logger.info(result_meta.summary())
            return []
            
        selected_indices = self._llm_select_batch(pre_filtered, category)
        survived = [pre_filtered[idx] for idx in selected_indices]
        
        # Step 3: Final ranking & limit
        # Sort by source weight (Tie-breaker)
        survived.sort(key=lambda x: x.source_weight, reverse=True)
        final = survived[:limit]
        
        result_meta.pass1_survived = len(pre_filtered)
        result_meta.pass2_selected = len(final)
        result_meta.model_used = "Gemini-1.5-Flash (Batch Scorer)"
        
        logger.info(result_meta.summary())
        return final
