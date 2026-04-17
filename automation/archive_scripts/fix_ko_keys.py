import os
import re

def fix_korean_keys(base_path):
    # 변환 맵
    key_map = {
        '제목:': 'title:',
        '날짜:': 'date:',
        '설명:': 'description:',
        '이미지:': 'image:',
        '클러스터:': 'clusters:',
        '카테고리:': 'categories:',
        '태그:': 'tags:',
        '주요 콘텐츠 여부:': 'featured:',
        '유형:': 'type:'
    }
    
    count = 0
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8-sig") as file:
                    content = file.read()
                
                new_content = content
                found = False
                for ko_key, en_key in key_map.items():
                    if ko_key in new_content:
                        new_content = new_content.replace(ko_key, en_key)
                        found = True
                
                if found:
                    with open(p, "w", encoding="utf-8-sig") as file:
                        file.write(new_content)
                    print(f"[키 교정 완료] {f}")
                    count += 1
    return count

if __name__ == "__main__":
    c = fix_korean_keys("content/ko")
    print(f"Total {c} files fixed.")
