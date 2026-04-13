import os

def rebuild_standard_indices():
    base = r'c:\AI\Antigravity\News'
    # 13개 표준 카테고리
    cats = {
        'llm-tech': 'LLM & 파운데이션 모델', 'future-sw': '미래 소프트웨어 & 클라우드', 
        'platform-biz': '빅테크 플랫폼 비즈니스', 'security-tech': '사이버 보안 & 암호학', 
        'chip-tech': '차세대 반도체 (HBM/PIM)', 'robot-tech': '로보틱스 & 자율주행', 
        'space-tech': '항공우주 & 위성 테크', 'bio-tech': '헬스케어 & 바이오 테크', 
        'energy-tech': '차세대 에너지 & 배터리', 'market-trend': '글로벌 마켓 트렌드', 
        'meta-tech': '메타버스 & AR/VR', 'game-tech': '게임 테크 & 엔진', 
        'spatial-tech': '공간 컴퓨팅 (Spatial)'
    }
    # 4대 클러스터
    clusters = {
        'intelligence': '인텔리전스 (AI/SW)', 'physical': '피지컬 (반도체/로봇)', 
        'strategy': '라이프 전략 (에너지/바이오)', 'digital': '디지털 (게임/가상세계)'
    }
    
    print(" [PROCESS] Forced Reconstruction of Standard Index Files...")
    # 카테고리 기지 건설
    for slug, title in cats.items():
        p = os.path.join(base, 'content', 'ko', 'categories', slug)
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, '_index.md'), 'w', encoding='utf-8') as f:
            f.write(f'---\ntitle: "{title}"\ndate: "2026-04-13"\n---\n')
        print(f"   [CREATED] category/{slug} -> {title}")
            
    # 클러스터 대문 건설
    for slug, title in clusters.items():
        p = os.path.join(base, 'content', 'ko', 'clusters', slug)
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, '_index.md'), 'w', encoding='utf-8') as f:
            f.write(f'---\ntitle: "{title}"\ndate: "2026-04-13"\n---\n')
        print(f"   [CREATED] cluster/{slug} -> {title}")

if __name__ == "__main__":
    rebuild_standard_indices()
