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

def audit_dir(base_path):
    stats = {
        'clusters': {},
        'categories': {},
        'files': []
    }
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                meta = get_meta(p)
                if meta:
                    cluster = meta.get("clusters", ["none"])[0]
                    category = meta.get("categories", ["none"])[0]
                    stats['clusters'][cluster] = stats['clusters'].get(cluster, 0) + 1
                    stats['categories'][category] = stats['categories'].get(category, 0) + 1
                    stats['files'].append({"name": f, "cluster": cluster, "category": category})
    return stats

ko = audit_dir("content/ko")
en = audit_dir("content/en")

print("--- CLUSTER COMPARISON ---")
all_clusters = set(list(ko['clusters'].keys()) + list(en['clusters'].keys()))
for c in sorted(all_clusters):
    print(f"[{c}] KO: {ko['clusters'].get(c, 0)} | EN: {en['clusters'].get(c, 0)}")

print("\n--- CATEGORY COMPARISON ---")
all_cats = set(list(ko['categories'].keys()) + list(en['categories'].keys()))
for cat in sorted(all_cats):
    print(f"[{cat}] KO: {ko['categories'].get(cat, 0)} | EN: {en['categories'].get(cat, 0)}")

# Find missing counterparts (simple filename match)
ko_files = {f['name'] for f in ko['files']}
en_files = {f['name'] for f in en['files']}

only_ko = ko_files - en_files
only_en = en_files - ko_files

print(f"\nOnly in KO: {len(only_ko)}")
print(f"Only in EN: {len(only_en)}")
