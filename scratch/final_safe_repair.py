import os
import re
import yaml
from pathlib import Path

# [V5.0] Ultimate Content Repair & Taxonomy Sync
POSTS_DIR = Path("c:/AI/Antigravity/News/content/ko/posts/2026/04")

CLUSTER_MAP = {
    "llm-tech": "intelligence", "ai-agent": "intelligence", "ai-policy": "intelligence", "future-sw": "intelligence",
    "semi-hbm": "physical", "hpc-infra": "physical", "robotics": "physical",
    "monetization": "strategy", "startups-vc": "strategy", "market-trend": "strategy",
    "game-tech": "digital", "spatial-tech": "digital", "space-tech": "physical", "chip-tech": "physical"
}

def repair_content():
    if not POSTS_DIR.exists():
        print(f" [!] Directory not found: {POSTS_DIR}")
        return

    files = list(POSTS_DIR.glob("*.md"))
    print(f" [PROCESS] Analyzing {len(files)} articles...")

    processed_count = 0
    unique_titles = {} # To handle duplicates: {title: (file_path, size)}

    for f in files:
        if f.name == "_index.md": continue
        
        # 1. Encoding Detection & Read
        content = ""
        for enc in ['utf-8-sig', 'utf-8', 'cp949', 'latin-1']:
            try:
                with open(f, 'r', encoding=enc) as file:
                    content = file.read()
                if "title:" in content: break
            except: continue
        
        if not content:
            print(f" [!] Failed to read: {f.name}")
            continue

        # 2. Extract Frontmatter
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if not match:
            print(f" [!] Invalid Frontmatter: {f.name}")
            continue

        header_raw = match.group(1)
        body = match.group(2)

        try:
            # Simple manual parsing to avoid YAML library encoding issues with corrupted text
            data = {}
            for line in header_raw.split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    k = parts[0].strip()
                    v = parts[1].strip().strip('"').strip("'").strip('[').strip(']')
                    data[k] = v
            
            title = data.get('title', f.stem)
            cat = data.get('categories', 'market-trend').lower().strip()
            
            # Handle potential list format "['cat']"
            cat = cat.replace('[', '').replace(']', '').replace("'", "").replace('"', '').split(',')[0].strip()
            
            # 3. Deduplication Logic
            if title in unique_titles:
                prev_path, prev_size = unique_titles[title]
                if f.stat().st_size > prev_size:
                    try: os.remove(prev_path)
                    except: pass
                    print(f" [RM] Duplicate (Smaller): {prev_path.name}")
                else:
                    try: os.remove(f)
                    except: pass
                    print(f" [RM] Duplicate (Smaller): {f.name}")
                    continue

            unique_titles[title] = (f, f.stat().st_size)

            # 4. Taxonomy Correction (FORCED EVAPORATION TO INTELLIGENCE)
            new_cluster = "intelligence"
            cat = "llm-tech"
            
            tags_raw = data.get("tags", "[]")
            # Clean and rebuild tags list securely
            t_items = [t.strip().strip('"').strip("'") for t in tags_raw.replace('[', '').replace(']', '').split(',')]
            tags_final = "[" + ", ".join([f'"{t}"' for t in t_items if t]) + "]"
            
            # 5. Rebuild Frontmatter safely
            new_header = []
            new_header.append('---')
            new_header.append(f'title: "{title}"')
            new_header.append(f'date: "{data.get("date", "2026-04-13T10:00:00+09:00")}"')
            new_header.append(f'description: "{data.get("description", "")}"')
            new_header.append(f'image: "{data.get("image", "/images/fallbacks/tech-biz.jpg")}"')
            new_header.append(f'clusters: ["{new_cluster}"]')
            new_header.append(f'categories: ["{cat}"]')
            new_header.append(f'tags: {tags_final}')
            new_header.append(f'featured: {data.get("featured", "false")}')
            new_header.append('---')
            
            final_content = "\n".join(new_header) + "\n" + body
            
            # 6. Save as clean UTF-8
            with open(f, 'w', encoding='utf-8') as file:
                file.write(final_content)
            processed_count += 1

        except Exception as e:
            print(f" [!] Error processing {f.name}: {e}")

    print(f" [SUCCESS] Total {processed_count} articles repaired and synced.")

if __name__ == "__main__":
    repair_content()
