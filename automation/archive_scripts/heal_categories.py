import os
import glob
import re

# 교정 매핑 테이블 (구 명칭 -> 신 명칭)
CATEGORY_MAP = {
    "게이밍-하드웨어": "하드웨어",
    "하드웨어": "하드웨어",
    "게임": "게임",
    "AI·신기술": "AI-기술",
    "AI 신기술": "AI-기술",
    "AI·뉴스": "AI-기술",
    "AI 뉴스": "AI-기술",
    "AI 에이전트": "AI-에이전트",
    "AI·에이전트": "AI-에이전트",
    "수익화 전략": "수익화-전략",
    "라이프·취미": "라이프-취미",
    "라이프 취미": "라이프-취미",
    "캠핑": "라이프-취미"
}

def heal_categories(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # categories: ["..."] 패턴 찾기 및 교정
        modified = False
        for old, new in CATEGORY_MAP.items():
            if old in content:
                content = content.replace(f'"{old}"', f'"{new}"')
                content = content.replace(f"'{old}'", f"'{new}'")
                modified = True
        
        if modified:
            with open(path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error healing {path}: {e}")
        return False

# 모든 마크다운 파일 전수 조사 및 치료
all_posts = glob.glob("content/posts/**/*.md", recursive=True)
healed_count = 0
for p in all_posts:
    if heal_categories(p):
        healed_count += 1

print(f"Successfully healed categories for {healed_count} posts.")
