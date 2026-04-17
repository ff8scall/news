import os
import glob
import re

def aggressive_repair(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        new_lines = []
        in_frontmatter = False
        frontmatter_markers = 0
        
        for line in lines:
            if line.strip() == "---":
                frontmatter_markers += 1
                new_lines.append(line)
                continue
            
            # Frontmatter 내부의 깨진 줄 수정
            if frontmatter_markers == 1:
                # 물음표가 너무 많거나 짝이 안 맞는 따옴표 수정
                if '????' in line or line.count('"') % 2 != 0:
                    # 따옴표 짝이 안 맞으면 강제로 닫아버리거나 해당 라인 초기화
                    line = re.sub(r'[\?]+', '', line) # 외계어 삭제
                    if line.count('"') % 2 != 0:
                        line = line.strip() + '"\n'
                new_lines.append(line)
            else:
                # 본문은 그대로 유지
                new_lines.append(line)
                
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Failed to fix {path}: {e}")
        return False

posts = glob.glob("content/posts/news/*.md")
fixed = 0
for p in posts:
    if aggressive_repair(p):
        fixed += 1

print(f"Aggressively repaired {fixed} posts.")
