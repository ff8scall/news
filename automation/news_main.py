import os
import time
import sys
from news_harvester import NewsHarvester
from ai_news_editor import NewsEditor
from history_manager import HistoryManager
from telegram_notifier import TelegramNotifier
from gatekeeper import FinalGatekeeper

def create_hugo_post(article):
    """최종 선정된 뉴스를 Hugo 포스팅으로 생성"""
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
    with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SUCCESS] Draft: {article['title']}")

def main():
    # 인자값에 따라 정밀 쿼터 관리
    is_night_mode = "--night" in sys.argv
    
    # [사용자 요청 반영] 야간에는 대량(50개), 주간에는 테스트 보존을 위해 소량(10개)
    article_limit = 50 if is_night_mode else 10
    
    harvester = NewsHarvester()
    editor = NewsEditor()
    history = HistoryManager()
    gatekeeper = FinalGatekeeper()
    notifier = TelegramNotifier()
    
    print(f"=== [V4.6] News Hub Starting (Security: HIGH / Limit: {article_limit}) ===")
    
    # 1. 뉴스 수집 (야간에만 그물을 크게 침)
    new_raw_news = harvester.fetch_all(limit_per_api=50 if is_night_mode else 5)
    
    # 2. 중복 처리
    new_articles = []
    seen_urls = set()
    for article in new_raw_news:
        url = article['url']
        if url not in seen_urls and not history.is_already_processed(url):
            new_articles.append(article)
            seen_urls.add(url)
    
    if not new_articles:
        if not is_night_mode: notifier.send_message("실시간 새로운 소식이 없습니다. 💤")
        return

    # 3. 1차 AI 편집 (정해진 쿼터 내에서만)
    new_articles = new_articles[:article_limit]
    print(f"[*] Processing {len(new_articles)} articles under Quota-Protection Mode.")
    
    batch_size = 10
    high_value_news = []
    
    for i in range(0, len(new_articles), batch_size):
        batch = new_articles[i : i + batch_size]
        reviews = editor.review_batch(batch)
        for rev in reviews:
            idx = rev.get('index')
            if idx is not None and isinstance(idx, int) and idx < len(batch):
                score = rev.get('score', 0)
                if score >= 7:
                    art = batch[idx]
                    art['summary'] = rev.get('summary', '요약 실패')
                    create_hugo_post(art)
                    history.add_to_history(art['url'], art['title'])
        if i + batch_size < len(new_articles): time.sleep(5)
            
    # 4. 최종 마이그레이션 및 검역 (마지막 품질 보증)
    gatekeeper.audit_and_migrate()

    # 5. 자동화 빌드 (야간 모드만)
    if is_night_mode:
        print("[*] Performing Night-Shift Build & Deploy...")
        os.system(f"powershell -Command \"& C:\\hugo_tmp\\hugo.exe --gc --cleanDestinationDir; git add .; git commit -m 'Auto Harvest (Nightly)'; git push origin main\"")

    # 6. 알림
    mode_str = "야간 수혈" if is_night_mode else "주간 정찰"
    msg = f"🛡️ **[{mode_str}] 완료**\n\n- 정예 포스팅 발행 성공\n- 테스트용 쿼터를 보존하며 실시간 반영되었습니다. 🛰️"
    notifier.send_message(msg)

if __name__ == "__main__":
    main()
