import os
import re
import yaml

def get_meta(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            if content.startswith("---"):
                parts = content.split("---")
                if len(parts) >= 3:
                    return yaml.safe_load(parts[1])
    except:
        pass
    return None

def audit_posts(base_path):
    stats = {'clusters': {}, 'categories': {}, 'total': 0, 'files': {}}
    for root, dirs, files in os.walk(base_path):
        for f in files:
            # _index.md 는 제외하고 순수 포스트만
            if f.endswith(".md") and not f.startswith("_index"):
                p = os.path.join(root, f)
                meta = get_meta(p)
                if meta:
                    cluster = meta.get("clusters", ["none"])[0]
                    category = meta.get("categories", ["none"])[0]
                    stats['clusters'][cluster] = stats['clusters'].get(cluster, 0) + 1
                    stats['categories'][category] = stats['categories'].get(category, 0) + 1
                    stats['files'][f] = {'cluster': cluster, 'category': category}
                    stats['total'] += 1
    return stats

ko = audit_posts("content/ko")
en = audit_posts("content/en")

print(f"TOTAL POSTS | KO: {ko['total']} | EN: {en['total']}")

print("\n--- CLUSTERS (POSTS ONLY) ---")
all_clusters = set(list(ko['clusters'].keys()) + list(en['clusters'].keys()))
for c in sorted(all_clusters):
    print(f"[{c}] KO: {ko['clusters'].get(c, 0)} | EN: {en['clusters'].get(c, 0)}")

# Find exact missing files by name
only_ko = set(ko['files'].keys()) - set(en['files'].keys())
only_en = set(en['files'].keys()) - set(ko['files'].keys())

if only_ko: print(f"\nMissing in EN: {only_ko}")
if only_en: print(f"\nMissing in KO: {only_en}")
