import os
import re

def shorten_title(title, limit=50):
    if len(title) <= limit:
        return title
    # 단순히 자르는 대신, 문장이 깔끔하게 끝나도록 처리
    short = title[:limit-3].strip() + "..."
    return short

def repair_all_titles(root_dir):
    print(f"[*] Auditing titles in {root_dir}...")
    count = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md") and "_index" not in file:
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 프론트매터의 title 추출
                title_match = re.search(r'^title:\s*"(.*)"', content, re.MULTILINE)
                if title_match:
                    original_title = title_match.group(1)
                    if len(original_title) > 50:
                        new_title = shorten_title(original_title)
                        new_content = content.replace(f'title: "{original_title}"', f'title: "{new_title}"')
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f" [FIXED] {file}: {len(original_title)} -> {len(new_title)} chars")
                        count += 1
    return count

if __name__ == "__main__":
    base_path = os.path.join(os.getcwd(), "content")
    fixed_ko = repair_all_titles(os.path.join(base_path, "ko"))
    fixed_en = repair_all_titles(os.path.join(base_path, "en"))
    print(f"[*] Total {fixed_ko + fixed_en} titles optimized.")
