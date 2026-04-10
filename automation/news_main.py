import os
import time
import sys
import glob
from news_harvester import NewsHarvester
from ai_news_editor import NewsEditor
from history_manager import HistoryManager
from telegram_notifier import TelegramNotifier
from gatekeeper import FinalGatekeeper

def count_all_posts():
    """블로그 내의 전체 마크다운 포스트 개수 계산"""
    posts = glob.glob("content/posts/**/*.md", recursive=True)
    # _index.md 같은 설정 파일 제외
    valid_posts = [p for p in posts if "_index" not in p]
    return len(valid_posts)

def create_hugo_post(article):
    """최종 선정된 뉴스를 풍성한 다층 구조로 생성 (원본+번역+인사이트)"""
    path = "content/posts/news" 
    os.makedirs(path, exist_ok=True)
    
    # 본문 요약 (메타 데이터용)
    clean_desc = article.get('summary', '')[:150].replace('\n', ' ')
    filename = f"news-{int(time.time())}.md"
    
    content = f"""---
title: "{article['korean_title']}"
date: "{time.strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{clean_desc}"
categories: ["AI·뉴스"]
tags: ["{article['source']}", "2026", "테크"]
image: "{article['urlToImage']}"
---

### 📡 AI 전문 편집장 3줄 요약
{article['summary']}

---

### 🌐 Original Article Summary
> {article.get('original_title', '')}
> 
> {article.get('original_description', 'No description available.')}

---

### 🇰🇷 한국어 번역 및 마이그레이션
{article.get('translation', '번역 중 오류가 발생했습니다.')}

---

### 💎 AI 편집장의 심층 분석 및 전망
{article.get('insight', '분석 중 오류가 발생했습니다.')}

---

**[원본 기사 보기]({article['url']})**
"""
    with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SUCCESS] Premium Column Posted: {article['korean_title']}")

def main():
    is_night_mode = "--night" in sys.argv
    article_limit = 50 if is_night_mode else 10 # 주간엔 10개만 정규 수집
    harvest_limit = 50 if is_night_mode else 5
    
    harvester = NewsHarvester()
    editor = NewsEditor()
    history = HistoryManager()
    gatekeeper = FinalGatekeeper()
    notifier = TelegramNotifier()
    
    print(f"=== [V5.0] Premium Magazine Engine Launch ===")
    
    # 1. 뉴스 수집
    new_raw_news = harvester.fetch_all(limit_per_api=harvest_limit)
    
    # 2. 중복 처리
    new_articles = []
    seen_urls = set()
    for article in new_raw_news:
        url = article['url']
        if url not in seen_urls and not history.is_already_processed(url):
            new_articles.append(article)
            seen_urls.add(url)
    
    if not new_articles:
        if not is_night_mode: notifier.send_message("🔍 실시간 새로운 정보가 감지되지 않았습니다. 🛰️")
        return

    # 3. AI 심층 편집 (원본 전달)
    new_articles = new_articles[:article_limit]
    print(f"[*] Deep-Editing {len(new_articles)} global articles...")
    
    batch_size = 5 # 심층 분석을 위해 배치를 줄임
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
                    # 원본 데이터와 AI 데이터를 결합
                    art.update({
                        'korean_title': rev.get('korean_title', art['title']),
                        'original_title': art['title'],
                        'original_description': art.get('description', ''),
                        'summary': rev.get('summary', ''),
                        'translation': rev.get('translation', ''),
                        'insight': rev.get('insight', ''),
                        'score': score
                    })
                    create_hugo_post(art)
                    history.add_to_history(art['url'], art['title'])
                    high_value_news.append(art)
        if i + batch_size < len(new_articles): time.sleep(5)
            
    # 4. 최종 게이트키핑 및 배포
    if high_value_news:
        gatekeeper.audit_and_migrate()
        if is_night_mode:
            os.system(f"powershell -Command \"& C:\\hugo_tmp\\hugo.exe --gc --cleanDestinationDir; git add .; git commit -m 'Release V5.0 Premium Contents'; git push origin main\"")

    # 5. 알림
    total_posts = count_all_posts()
    mode_str = "새벽 정규 수집" if is_night_mode else "주간 원격 제어"
    msg = f"🏛️ **[{mode_str}] V5.0 마감 보고**\n\n- 발행 포스트: {len(high_value_news)}건\n- 누적 포스트: {total_posts}개\n\n원본 보존 및 심층 분석이 완료되었습니다. 🚀"
    notifier.send_message(msg)

if __name__ == "__main__":
    main()
