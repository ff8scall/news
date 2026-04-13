import os
import re

def holy_content_sync():
    base_path = r"c:\AI\Antigravity\News"
    posts_dir = os.path.join(base_path, "content", "ko", "posts", "2026", "04")
    
    # 1. 해시 ID 기반 중복 제거
    seen_ids = set()
    files = sorted(os.listdir(posts_dir)) # 정렬하여 안정적인 중칭 선택
    
    print(f" [PHASE 3] Deduplicating {len(files)} articles...")
    for filename in files:
        if not filename.endswith(".md"): continue
        file_id = filename.split('-')[-1].replace('.md', '')
        
        path = os.path.join(posts_dir, filename)
        if len(file_id) == 6:
            if file_id in seen_ids:
                os.remove(path) # 중복 제거
            else:
                seen_ids.add(file_id)
        else:
            # 해시가 없는 기사는 일단 보존하되 정규화 대상에 포함
            pass

    # 2. 살아남은 기사 정교화 (Holy Reconstruction)
    reborn_files = os.listdir(posts_dir)
    print(f" [PHASE 3] Rebuilding frontmatter for {len(reborn_files)} unique articles...")
    
    # 키워드 기반 분류 룰 (정밀화)
    RULES = [
        (r"반도체|칩|HBM|Intel|NVIDIA|CPU|Samsung|TSMC", "physical", "chip-tech"),
        (r"로봇|자율주행|Tesla|FSD|Robot", "physical", "robot-tech"),
        (r"우주|Artemis|위성|달|NASA|Space", "physical", "space-tech"),
        (r"에너지|배터리|EV|전기|Altilium", "strategy", "energy-tech"),
        (r"바이오|헬스|의료|Drug|Clinical", "strategy", "bio-tech"),
        (r"트렌드|시장|분석|Market|Pricing|Belkin|Ricoh", "strategy", "market-trend"),
        (r"게임|Gamer|Epic|Steam|Nintendo|Bethesda", "digital", "game-tech"),
        (r"Vision Pro|Spatial|VR|AR|Metaverse", "digital", "spatial-tech"),
        (r"보안|암호|해킹|Cyber|Security", "intelligence", "security-tech"),
        (r"Cloud|SaaS|소프트웨어|Chrome|Target Display", "intelligence", "future-sw"),
        (r"플랫폼|비즈니스|Strategy|TikTok", "intelligence", "platform-biz"),
        (r"AI|LLM|GPT|Gemini|Claude", "intelligence", "llm-tech")
    ]

    for filename in reborn_files:
        path = os.path.join(posts_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        content_all = "".join(lines)
        
        # 최적의 슬러그 판별
        c_slug = "intelligence"; cat_slug = "llm-tech" # 기본값
        found = False
        for pattern, cs, cat in RULES:
            if re.search(pattern, content_all, re.IGNORECASE):
                c_slug = cs; cat_slug = cat
                found = True
                break
        
        # 파일 내용 재작성
        new_lines = []
        for line in lines:
            # 기존 분류 라인들 무조건 무시하고 새로 박음
            if line.strip().startswith("clusters:"):
                new_lines.append(f'clusters: ["{c_slug}"]\n')
            elif line.strip().startswith("categories:"):
                new_lines.append(f'categories: ["{cat_slug}"]\n')
            elif line.strip().startswith("tags:"):
                # 태그 경량화 (윈도우 파일 에러 방지용)
                new_lines.append(f'tags: ["테크전략", "인사이트"]\n')
            else:
                new_lines.append(line)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    print(f" [SUCCESS] Phase 3 Finalized. Total {len(reborn_files)} articles normalized.")

if __name__ == "__main__":
    holy_content_sync()
