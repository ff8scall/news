import os
import re

content_dirs = ["content/ko/posts", "content/en/posts"]

print("=== Starting Category Consolidation (game -> gaming) ===")

for base_dir in content_dirs:
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # categories: ["game"] -> categories: ["gaming"]
                new_content = content.replace('categories: ["game"]', 'categories: ["gaming"]')
                
                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"[*] Updated: {file}")

print("=== Done ===")
