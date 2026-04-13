import os

def second_genesis():
    base_path = r"c:\AI\Antigravity\News"
    posts_dir = os.path.join(base_path, "content", "ko", "posts", "2026", "04")
    
    # 1. 해시 ID 기반 중복 제거 및 리스트 확보
    seen_ids = set()
    unique_posts = []
    
    print(" [PHASE 1] Deduplicating 192 articles...")
    for filename in sorted(os.listdir(posts_dir)):
        if not filename.endswith(".md"): continue
        # 해시 ID 추출 (예: xxxxx-8ca5d9.md -> 8ca5d9)
        file_id = filename.split('-')[-1].replace('.md', '')
        if len(file_id) == 6 and file_id not in seen_ids:
            seen_ids.add(file_id)
            unique_posts.append(filename)
        elif len(file_id) != 6: # 해시가 없는 특이 케이스도 일단 보존
            unique_posts.append(filename)

    # 2. 비선택 기사 삭제
    all_files = os.listdir(posts_dir)
    for f in all_files:
        if f not in unique_posts:
            os.remove(os.path.join(posts_dir, f))
    
    print(f"   [DONE] Kept {len(unique_posts)} unique articles. Deleted others.")

    # 3. 파일명 정규화 및 성역화(Holy Recon)
    print("\n [PHASE 2] Renaming and Holy Reconstruction...")
    for filename in os.listdir(posts_dir):
        old_path = os.path.join(posts_dir, filename)
        
        # 파일명 변경 (xxxxx-8ca5d9.md -> xxxxx-8ca5d9-strategy-analysis.md)
        new_name = filename.replace('.md', '-strategy-analysis.md')
        new_path = os.path.join(posts_dir, new_name)
        
        with open(old_path, 'r', encoding='utf-8') as f: lines = f.readlines()
        
        c_slug = "intelligence"; cat_slug = "llm-tech"
        content_all = "".join(lines).lower()
        
        if any(x in content_all for x in ["반도체", "칩", "chip", "robot", "robotics", "artemis", "삼성", "tsmc"]):
            c_slug = "physical"; cat_slug = "chip-tech"
        elif any(x in content_all for x in ["에너지", "배터리", "바이오", "의료", "헬스", "market"]):
            c_slug = "strategy"; cat_slug = "market-trend"
        elif any(x in content_all for x in ["게임", "game", "epic", "disney", "vr", "metaverse"]):
            c_slug = "digital"; cat_slug = "game-tech"

        new_lines = []
        for line in lines:
            if line.strip().startswith("clusters:"):
                new_lines.append(f'clusters: ["{c_slug}"]\n')
            elif line.strip().startswith("categories:"):
                new_lines.append(f'categories: ["{cat_slug}"]\n')
            elif line.strip().startswith("tags:"):
                new_lines.append(f'tags: ["테크전략", "인사이트"]\n')
            else:
                new_lines.append(line)
        
        with open(old_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        os.rename(old_path, new_path)
        print(f"   [REBORN] {new_name}")

if __name__ == "__main__":
    second_genesis()
