import os
import shutil

def total_purge():
    base_path = r"c:\AI\Antigravity\News"
    en_posts_dir = os.path.join(base_path, "content", "en", "posts")
    ko_cats_dir = os.path.join(base_path, "content", "ko", "categories")
    en_cats_dir = os.path.join(base_path, "content", "en", "categories")
    
    # 표준 13개 카테고리 슬러그
    STANDARDS = [
        "llm-tech", "future-sw", "platform-biz", "security-tech",
        "chip-tech", "robot-tech", "space-tech",
        "bio-tech", "energy-tech", "market-trend",
        "meta-tech", "game-tech", "spatial-tech"
    ]

    print(" [PHASE 4] Total Purge Commencing...")

    # 1. 영문 기사 소탕 (분류 오염 방지)
    if os.path.exists(en_posts_dir):
        shutil.rmtree(en_posts_dir)
        os.makedirs(en_posts_dir, exist_ok=True)
        print("   [DONE] English posts purged.")

    # 2. 비표준 카테고리 소탕 (유령 버튼 방지)
    for cats_path in [ko_cats_dir, en_cats_dir]:
        if not os.path.exists(cats_path): continue
        for d in os.listdir(cats_path):
            if d not in STANDARDS:
                dir_to_rem = os.path.join(cats_path, d)
                if os.path.isdir(dir_to_rem):
                    shutil.rmtree(dir_to_rem)
                    print(f"   [DONE] Purged alien category: {d}")

    # 3. 빌드 캐시 소각 (과거의 망령 방지)
    for folder in ["public", "resources"]:
        p = os.path.join(base_path, folder)
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"   [DONE] Cache {folder} nuked.")

    print(" [SUCCESS] Phase 4 Total Purge Complete.")

if __name__ == "__main__":
    total_purge()
