import os
import re

def find_missing_meta(base_path):
    results = []
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8-sig") as file:
                    content = file.read()
                    # cluster가 없거나 none인 경우
                    is_missing = False
                    if "clusters:" not in content:
                        is_missing = True
                    elif re.search(r'clusters:\s*\[\s*\"?none\"?\s*\]', content):
                        is_missing = True
                    elif re.search(r'clusters:\s*\[\s*\]', content):
                        is_missing = True
                        
                    if is_missing:
                        results.append(p)
    return results

missing = find_missing_meta("content/ko")
print(f"Total Missing in KO: {len(missing)}")
for m in missing:
    print(m)
