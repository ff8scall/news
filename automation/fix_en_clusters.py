import os

def fix_clusters(base_path):
    count = 0
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8-sig") as file:
                    content = file.read()
                
                # 대소문자 및 괄호 무관하게 Intelligence를 ai-models-tools로 교체
                if 'clusters: ["Intelligence"]' in content or "clusters: ['Intelligence']" in content:
                    new_content = content.replace('clusters: ["Intelligence"]', 'clusters: ["ai-models-tools"]')
                    new_content = new_content.replace("clusters: ['Intelligence']", 'clusters: ["ai-models-tools"]')
                    with open(p, "w", encoding="utf-8-sig") as file:
                        file.write(new_content)
                    print(f"[교정 완료] {f}")
                    count += 1
    return count

print(f"Fixed {fix_clusters('content/en')} files.")
