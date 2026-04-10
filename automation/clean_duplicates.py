import os
import re
import sys
import io

# Windows에서 한글 및 특수기호 출력 오류 방쇄
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def clean_duplicates():
    posts_dir = "content/posts"
    titles = {}
    deleted_count = 0

    print("[*] Scanning for duplicate titles...")
    
    # 1. 전수 조사
    for root, dirs, files in os.walk(posts_dir):
        for file in files:
            if not file.endswith(".md"): continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 제목 추출 (title: "...")
                    match = re.search(r'title:\s*"(.*?)"', content)
                    if not match: continue
                    title = match.group(1)
                    
                    if title not in titles:
                        titles[title] = []
                    titles[title].append(path)
            except: continue

    # 2. 중복 제거 (others 폴더나 루트에 있는 것을 우선 삭제)
    for title, paths in titles.items():
        if len(paths) > 1:
            print(f"[DUPLICATE] \"{title}\" found in {len(paths)} locations.")
            # 정렬하여 우선순위 결정 (카테고리 폴더에 있는 것을 남김)
            # others/ 혹은 content/posts/에 바로 있는 것은 삭제 대상 1순위
            paths.sort(key=lambda x: ("others" in x or os.path.dirname(x) == posts_dir), reverse=True)
            
            # 하나만 남기고 모두 삭제
            to_keep = paths.pop(-1)
            print(f"  [KEEP] {to_keep}")
            for p in paths:
                print(f"  [DELETE] {p}")
                os.remove(p)
                deleted_count += 1
    
    print(f"\n[FINISH] Cleaned {deleted_count} duplicate files.")

if __name__ == "__main__":
    clean_duplicates()
