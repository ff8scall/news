import os
import time
from news_harvester import NewsHarvester
from ai_news_editor import NewsEditor
from history_manager import HistoryManager

def create_hugo_post(article):
    """최종 선정된 뉴스를 Hugo 포스팅으로 생성"""
    # 2026 리뉴얼 계층 구조 반영: 모든 뉴스는 news 폴더에 통합 관리
    path = "content/posts/news" 
    os.makedirs(path, exist_ok=True)
    
    clean_desc = article['summary'][:150].replace('\n', ' ')
    filename = f"news-{int(time.time())}.md"
    content = f"""---
title: "{article['title']}"
date: "{time.strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{clean_desc}"
categories: ["AI·뉴스"]
tags: ["{article['source']}", "2026", "테크"]
image: "{article['urlToImage']}"
---

### 📡 AI 전문 편집장 3줄 요약

{article['summary']}

---

**[원본 기사 보기]({article['url']})**
"""
    # 유니크한 파일명을 위해 짧은 딜레이 방지용으로 타임스탬프에 인덱스 추가 가능
    with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SUCCESS] Posted: {article['title']}")

def main():
    harvester = NewsHarvester()
    editor = NewsEditor()
    history = HistoryManager()
    
    print("=== [V3.0] AI Tech Magazine News Hub Starting ===")
    
    # 1. 뉴스 수집 (Global)
    new_raw_news = harvester.fetch_all()
    
    # 2. 중복 처리
    new_articles = []
    seen_urls = set()
    for article in new_raw_news:
        url = article['url']
        if url not in seen_urls and not history.is_already_processed(url):
            new_articles.append(article)
            seen_urls.add(url)
    
    if not new_articles:
        print("[!] No new news found. System standby.")
        return

    # 3. 정예 30선 제한 및 배치 리뷰
    new_articles = new_articles[:30]
    print(f"[*] Starting Batch Review for {len(new_articles)} articles.")
    
    batch_size = 10
    high_value_news = []
    
    for i in range(0, len(new_articles), batch_size):
        batch = new_articles[i : i + batch_size]
        print(f"[*] Batch {i//batch_size + 1} processing...")
        reviews = editor.review_batch(batch)
        
        for rev in reviews:
            idx = rev.get('index')
            if idx is not None and isinstance(idx, int) and idx < len(batch):
                score = rev.get('score', 0)
                if score >= 7:
                    art = batch[idx]
                    art['score'] = score
                    art['summary'] = rev.get('summary', '요약 실패')
                    high_value_news.append(art)
                    history.add_to_history(art['url'], art['title'])
        
        if i + batch_size < len(new_articles):
            print("[WAIT] Throttling 5s...")
            time.sleep(5)
            
    # 4. 발행
    print(f"\n[*] Final Selection: {len(high_value_news)} gems found.")
    for art in high_value_news:
        create_hugo_post(art)
        # 파일명 겹침 방지 (초당 여러 개 생성 방지)
        time.sleep(0.1) 

    print("=== Cycle Completed ===")

if __name__ == "__main__":
    main()
