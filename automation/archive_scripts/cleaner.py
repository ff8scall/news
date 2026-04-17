import os
import re

posts_dir = 'content/posts'
files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]

processed = []
for f in files:
    try:
        with open(os.path.join(posts_dir, f), 'r', encoding='utf-8') as file:
            content = file.read()
            # 프론트매터 추출
            title_match = re.search(r'title:\s*\"(.*)\"', content)
            cat_match = re.search(r'categories:\s*\[\"(.*)\"\]', content)
            
            if title_match and cat_match:
                processed.append({
                    'file': f,
                    'title': title_match.group(1).strip(),
                    'category': cat_match.group(1).strip(),
                    'size': len(content)
                })
    except Exception as e:
        print(f"Error reading {f}: {e}")

# 제목 기준으로 중복 제거 (가장 내용이 많은 것 선택)
best_files = {}
for p in processed:
    title = p['title']
    if title not in best_files or p['size'] > best_files[title]['size']:
        best_files[title] = p

# 실제 파일 정리
kept_files = {p['file'] for p in best_files.values()}
removed_count = 0

for f in files:
    if f not in kept_files:
        # 이전에 우리가 직접 만든 중요 파일은 제외 (auto-나 숫자로 시작하는 것들만 정리)
        if f.startswith('auto-') or f[0].isdigit():
            os.remove(os.path.join(posts_dir, f))
            removed_count += 1

print(f"=== Clean Up Result ===")
print(f"Total Processed: {len(processed)}")
print(f"Duplicates Removed: {removed_count}")
print(f"Final Starters: {len(best_files)}")
print("\n--- Final Content List (Grouped by Category) ---")

final_sorted = sorted(best_files.values(), key=lambda x: x['category'])
for p in final_sorted:
    # 안전한 출력을 위해 인코딩 오류 발생 가능한 문자 제거/대체
    safe_title = p['title'].encode('ascii', 'ignore').decode('ascii')
    if not safe_title: safe_title = "[Korean/Special Title]"
    print(f"[{p['category']}] {safe_title}")
