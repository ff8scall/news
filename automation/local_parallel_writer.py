import os
import sys
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# AIWriter 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def generate_local_article(topic, cluster, category):
    writer = AIWriter()
    print(f"[집필 시작] {topic}")
    
    # 1. 영문 기사 생성
    en_prompt = f"""
[TASK]
Write a professional technical news article in English about: "{topic}"
Role: Senior Tech Journalist for Lego-Sia Intelligence.
Tone: Sophisticated, data-driven, professional.
No emojis.
Structure:
- Title
- Description (Short)
- Content (Structured with ## headers)

[METADATA]
Cluster: {cluster}
Category: {category}
Date: 2026-04-14T11:00:00Z
"""
    en_raw = writer.generate_content(en_prompt, model="gemma4:latest")
    
    # 2. 한국어 번역 생성
    ko_prompt = f"""
[TASK]
Translate this technical article into professional Korean.
Source:
{en_raw}

[STRICT RULES]
- Professional "입니다" style.
- ZERO emojis.
- Keep YAML keys in English.
"""
    ko_raw = writer.generate_content(ko_prompt, model="gemma4:latest")
    
    # 3. 파일 저장 처리 (Helper)
    def clean_and_save(raw, lang):
        # YAML Frontmatter 생성 (필요 시 raw 분석하여 추출)
        title_match = re.search(r'Title:\s*(.*)', raw)
        title = title_match.group(1).strip('"') if title_match else topic
        desc_match = re.search(r'Description:\s*(.*)', raw)
        desc = desc_match.group(1) if desc_match else title
        
        slug = re.sub(r'[^a-z0-9]', '-', topic.lower())[:50].strip('-')
        
        frontmatter = f"""---
title: "{title}"
date: "2026-04-14T11:00:00Z"
description: "{desc}"
clusters: ["{cluster}"]
categories: ["{category}"]
type: "posts"
---

"""
        content = raw.split("Content:")[-1] if "Content:" in raw else raw
        content = re.sub(r'^```(markdown)?\n', '', content)
        content = re.sub(r'\n```$', '', content)
        if "---" in content: content = content.split("---")[-1]
        
        full_md = frontmatter + content.strip()
        
        path = f"content/{lang}/posts/2026/04/14/{slug}.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write(full_md)
        return path

    en_path = clean_and_save(en_raw, "en")
    ko_path = clean_and_save(ko_raw, "ko")
    print(f"[완료] {topic} -> {en_path}")

def main():
    with open("automation/temp_topics.json", "r", encoding="utf-8") as f:
        topics = json.load(f)
    
    tasks = []
    # Hardware
    for t in topics['hardware']: tasks.append((t, "gpu-hardware", "gpu-chips"))
    # Gaming
    for t in topics['gaming']: tasks.append((t, "ai-gaming", "game-optimization"))
    
    print(f"--- 5중 병렬 집필 시스템 가동 (총 {len(tasks)}건) ---")
    with ThreadPoolExecutor(max_workers=5) as executor:
        for topic, cluster, category in tasks:
            executor.submit(generate_local_article, topic, cluster, category)

if __name__ == "__main__":
    main()
