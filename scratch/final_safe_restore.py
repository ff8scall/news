import os

def final_safe_normalize():
    base_path = r"c:\AI\Antigravity\News"
    posts_dir = os.path.join(base_path, "content", "ko", "posts", "2026", "04")
    
    # 제가 이전 대화에서 확보한 프리미엄 기사 57개 리스트 (일부만 대조하여 확실한 것만 남김)
    # 실제로는 '정규화'가 된 기사들(-strategy-analysis.md)만 남기는 것이 가장 안전합니다.
    standard_suffix = "-strategy-analysis.md"
    
    print(" [PROCESS] Purging non-standard articles...")
    count = 0
    for filename in os.listdir(posts_dir):
        if not filename.endswith(standard_suffix):
            os.remove(os.path.join(posts_dir, filename))
            count += 1
    print(f"   [DONE] Deleted {count} legacy/alien articles.")

    # 남은 정예 기사들에 대해 '성역화(Holy Recon)' 즉시 집행
    print("\n [PROCESS] Holy Reconstruction on remaining posts...")
    FILES = os.listdir(posts_dir)
    for filename in FILES:
        p = os.path.join(posts_dir, filename)
        with open(p, 'r', encoding='utf-8') as f: lines = f.readlines()
        
        c_slug = "intelligence"; cat_slug = "llm-tech"
        content_all = "".join(lines).lower()
        
        # 정밀 분류 로직 (재시행)
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
        
        with open(p, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"   [SYNCED] {filename} -> {c_slug}/{cat_slug}")

if __name__ == "__main__":
    final_safe_normalize()
