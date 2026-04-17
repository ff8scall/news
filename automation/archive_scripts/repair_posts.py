import os
import glob

def repair_post(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 1. 중복된 verified: true 및 파손된 구분선 제거
        lines = content.splitlines()
        clean_lines = []
        frontmatter_count = 0
        has_verified = False
        
        for line in lines:
            if line.strip() == "---":
                frontmatter_count += 1
                clean_lines.append(line)
                if frontmatter_count == 1:
                    clean_lines.append("verified: true")
                continue
            
            if "verified: true" in line:
                continue # 이미 위에서 넣었으므로 무시
            
            clean_lines.append(line)
        
        # 2. 강제로 다시 쓰기 (교정된 UTF-8)
        new_content = "\n".join(clean_lines)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error repairing {path}: {e}")
        return False

# 뉴스 폴더의 모든 마크다운 파일 수리
posts = glob.glob("content/posts/news/*.md")
repaired = 0
for p in posts:
    if repair_post(p):
        repaired += 1

print(f"Successfully repaired {repaired} posts.")
