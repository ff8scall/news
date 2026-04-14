import os
import re
import logging
from datetime import datetime
from ai_writer import AIWriter

logger = logging.getLogger("LegoSia.GuideEditor")

class GuideEditor:
    """[V9.1] Ultimate Professional Engine: Pure Logic, No Emojis, Image Prompt Preservation"""
    def __init__(self, model_name="gemma4:latest", writer=None):
        self.model_name = model_name
        self.writer = writer if writer else AIWriter()

    def write_english_guide(self, news_draft):
        """1단계: 영문 마스터 가이드 생성 (Zero Emojis, Strong Structure)"""
        title = news_draft.get('kor_title', 'Solution Implementation')
        
        prompt = f"""
[ROLE]
Senior Solutions Architect. Use formal, professional English.

[TOPIC]
{title}

[STRICT GUIDELINES]
1. NO EMOJIS: Do not use any icons or emojis.
2. CONTENT: Provide deep technical steps with code blocks.
3. IMAGE PROMPT: Create a professional 3D technical illustration prompt about {title}. Focus on geometry, light, and technology. NO HUMANS.
4. FORMAT: Start with --- YAML ---.

[SKELETON]
---
title: "Practical Guide: {title}"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "Professional technical summary."
type: "posts"
clusters: ["guides"]
categories: ["tutorials"]
tags: ["tech", "guide"]
difficulty: "Advanced"
image_prompt_core: "High-end 3D render of..."
---

## Overview
## Phase 1. Environment Configuration
## Phase 2. Core Implementation
## Phase 3. Validation
"""
        raw_en = self.writer.generate_content(prompt, model=self.model_name)
        return self._clean_markdown(raw_en)

    def translate_to_korean(self, en_markdown):
        """2단계: 1:1 한글화 (이모지 완전 소거, 이미지 프롬프트 영문 유지)"""
        if not en_markdown: return None
        
        # [V9.1] 이미지 프롬프트는 번역하지 말고 그대로 두라는 지시 추가
        prompt = f"""
[TASK]
Translate this technical document into professional Korean.

[IMPORTANT RULES]
1. ZERO EMOJIS: Delete all emojis. No checkmarks, no crosses.
2. YAML KEYS: NEVER translate YAML keys (title, date, description, image, etc.). Keep them exactly as they are in English.
3. IMAGE PROMPT: DO NOT translate the 'image_prompt_core' value. Keep it in English.
4. HEADERS: Use only Korean for headers. (e.g., '## 개요' instead of '## 개요 (Overview)')
4. 1:1 CLONE: Translate every section and code comment. Do not shorten.
5. TONE: Professional academic style (~입니다).

[DOCUMENT]
{en_markdown}
"""
        raw_ko = self.writer.generate_content(prompt, model=self.model_name)
        return self._clean_markdown(raw_ko)

    def _clean_markdown(self, raw_text):
        if not raw_text: return ""
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(markdown)?\n', '', clean)
            clean = re.sub(r'\n```$', '', clean)
        if "---" in clean:
            clean = clean[clean.find("---"):]
        
        # [V9.1] 물리적 이모지 및 특수 조합 제거 (정규식 강화)
        clean = re.sub(r'[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s.,;:!?()\[\]{}<>#*~\-_/`\'"]', '', clean)
        # 메타 발언 제거
        clean = re.sub(r'\(Decision.*?\)', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\(Self-Correction.*?\)', '', clean, flags=re.IGNORECASE)
        # [V9.2] 빈 섹션 또는 'None'인 섹션 삭제 (예: ## Summary \n None)
        clean = re.sub(r'##.*?\n+(None|N/A|참고 사항 없음)\s*(?=\n|#|$)', '', clean, flags=re.IGNORECASE | re.DOTALL)
        # 중복 개행 정리
        clean = re.sub(r'\n{3,}', '\n\n', clean)
        
        return clean.strip()
