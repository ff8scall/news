import os
import sys
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from automation.news_harvester import NewsHarvester

def test_images():
    harvester = NewsHarvester()
    print("[*] Testing image harvesting (FORCE MODE: 48H Back)...")
    
    # 강제로 시간 범위를 넓힘
    sort_by = "publishedAt"
    from_time = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S')
    
    # 하드웨어 카테고리 하나만 집중 타겟팅
    query = "Nvidia Blackwell GPU AI"
    print(f"[*] Querying: {query} since {from_time}")
    
    # NewsAPI 직접 테스트
    res = harvester._fetch_newsapi(query, "하드웨어", 5)
    
    if not res:
        print("[!] No results even with broad search. Checking other APIs...")
        res = harvester._fetch_gnews(query, "하드웨어", 5)

    found_count = 0
    for i, article in enumerate(res):
        img = article.get('urlToImage')
        if img and img.startswith('http'):
            found_count += 1
        print(f"[{i}] Title: {article['title'][:40]}...")
        print(f"    Source: {article['source']}")
        print(f"    Image: {img or 'EMPTY'}")
        print("-" * 20)
    
    print(f"[*] Analysis: {found_count}/{len(res)} articles have images.")

if __name__ == "__main__":
    test_images()
