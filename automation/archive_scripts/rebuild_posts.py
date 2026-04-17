import os
import glob
from datetime import datetime

def rebuild_frontmatter(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 기사 본문 찾기 (두 번째 --- 이후)
        parts = content.split('---')
        if len(parts) < 3:
            return False # 형식이 너무 많이 파손됨
            
        body = parts[2].strip()
        filename = os.path.basename(path).replace(".md", "")
        
        # 표준 규격의 새로운 FrontMatter 생성
        new_frontmatter = f"""---
verified: true
title: "Global News Update ({filename})"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "AI-powered global news summary and analysis."
categories: ["AI·신기술"]
tags: ["AI", "Tech", "News"]
---

"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_frontmatter + body)
        return True
    except Exception as e:
        print(f"Error rebuilding {path}: {e}")
        return False

posts = glob.glob("content/posts/news/*.md")
rebuilt = 0
for p in posts:
    if rebuild_frontmatter(p):
        rebuilt += 1

print(f"Successfully rebuilt {rebuilt} news posts.")
