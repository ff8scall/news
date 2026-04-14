import os
import re
import logging
from datetime import datetime
from ai_writer import AIWriter

logger = logging.getLogger("LegoSia.GuideEditor")

class GuideEditor:
    """[V7.3] Anti-Laziness Translation Pipeline: EN 1:1 Clone to KO"""
    def __init__(self, model_name="gemma4:latest", writer=None):
        self.model_name = model_name
        self.writer = writer if writer else AIWriter()

    def write_english_guide(self, news_draft):
        """1단계: 최고의 지능으로 영문 오리지널 가이드 생성"""
        title = news_draft.get('kor_title', 'Strategic Guide')
        tech_context = news_draft.get('kor_content', 'Standard technical implementation.')
        
        prompt = f"""
[PERSONA]
You are a 10-year senior engineer and top-tier technical instructor.

[ABSOLUTE CONSTRAINTS]
1. Output ONLY Markdown format. NO JSON.
2. Skip greetings. Start directly with the YAML frontmatter.
3. Include specific CLI commands and [Expected Results] for every step.
4. Generate a 1-sentence English prompt for the thumbnail image in 'image'. 
   - RULE: MUST be abstract 3D objects and data-centric flow.
   - FORBIDDEN: No humans, no robots, no text, no screens, no keyboards, no faces.

[OUTPUT SKELETON]
---
title: "[Practical Guide] {title} Implementation"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "How to achieve the goal in 1 line."
type: "posts"
clusters: ["guides"]
categories: ["tutorials"]
tags: ["guide", "tutorial"]
difficulty: "Advanced"
time_to_complete: "15 minutes"
image_prompt_core: "Glowing crystalline neural nodes connected by thin data streams, neon blue and deep purple"
---

## 🎯 Overview
(Technical objectives)

## 🚀 Phase 1. Infrastructure Setup
* **Step 1-1.** Action description
  * `command here`
  * **Expected Result:** ...

[TARGET TOPIC]: {title}
[TECHNICAL CONTEXT]: {tech_context}
"""
        raw_en = self.writer.generate_content(prompt, model=self.model_name)
        return self._clean_markdown(raw_en)

    def translate_to_korean(self, en_markdown):
        """2단계: [매우 중요] 생략 없는 1:1 완벽 번역 강제 (Anti-Laziness)"""
        if not en_markdown: return None
        
        prompt = f"""
[TASK]
Translate the following English technical guide into highly professional Korean.

[STRICT RULES - ANTI-LAZINESS]
1. 1:1 FULL TRANSLATION: You MUST translate every single section, phase, and step. DO NOT skip, summarize, or omit anything.
2. CODE PRESERVATION: Keep all Markdown code blocks (```bash, etc.), CLI commands, and technical terms exactly as they are in English.
3. TONE: Use a clean, professional Korean tone (e.g., "~를 실행하십시오", "다음 명령어를 입력합니다").
4. NO EMOJIS: Maintain the exact formatting (---, >, *, etc.).
5. YAML FRONTMATTER: Maintain the exact YAML structure, but translate the 'title' and 'description' values into Korean.

[ENGLISH GUIDE SOURCE]
{en_markdown}
"""
        raw_ko = self.writer.generate_content(prompt, model=self.model_name)
        return self._clean_markdown(raw_ko)

    def _clean_markdown(self, raw_text):
        """마크다운 백틱 클리닝 및 안전 파싱 (V7.3)"""
        if not raw_text: return ""
        clean = raw_text.strip()
        
        # ```markdown 또는 ``` 래핑 제거 로직 강화
        if clean.startswith("```"):
            clean = re.sub(r'^```(markdown)?\n', '', clean)
            clean = re.sub(r'\n```$', '', clean)
        
        # 잡설 제거 (첫 번째 --- 지점부터 시작)
        if "---" in clean:
            clean = clean[clean.find("---"):]
            
        return clean.strip()
