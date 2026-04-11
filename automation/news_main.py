import os
import time
import sys
import json
import re
import glob
import random
from datetime import datetime
from news_harvester import NewsHarvester
from ai_news_editor import NewsEditor
from history_manager import HistoryManager
from indexnow_service import notify_indexnow
from ai_reviewer import EditorInChief
from telegram_remote import TelegramRemote # [V10.8] 텔레그램 연동

import requests
import subprocess

def download_image(original_url, category_slug, slug):
    """
    1차: 원본 뉴스 이미지 시도
    2차: 실패 시 카테고리별 전용 폴백 이미지 사용
    3차: 최후 수단으로 AI 생성 시도
    """
    save_path = os.path.join("static", "images", f"{slug}.jpg")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # [1단계] 원본 원고 이미지 시도
    if original_url and original_url.startswith("http"):
        try:
            print(f" [*] Attempting to download original image: {original_url[:50]}...")
            response = requests.get(original_url, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return f"/images/{slug}.jpg"
        except Exception as e:
            print(f" [!] Original image download failed: {e}")

    # [2단계] 카테고리별 폴백 이미지 (단, 파일이 실제 존재할 때만)
    fallback_path = f"static/images/fallbacks/{category_slug}.jpg"
    if os.path.exists(fallback_path):
        return f"/images/fallbacks/{category_slug}.jpg"

    # [3단계] AI 생성 (Pollinations AI)
    try:
        seed_val = sum(ord(c) for c in slug) % 1000000
        prompt = f"Futuristic technology concept for {category_slug}"
        ai_url = f"https://image.pollinations.ai/prompt/{prompt}?width=1080&height=720&nologo=true&seed={seed_val}"
        response = requests.get(ai_url, timeout=20)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return f"/images/{slug}.jpg"
    except:
        pass

    return "/images/fallback-default.jpg"

def sanitize_slug(title):
    """영문 제목을 기반으로 URL 친화적인 파일명 생성"""
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', title).lower()
    return re.sub(r'\s+', '-', clean).strip('-')[:50]

def create_hugo_post(article, lang='ko'):
    """[V10.1] 날짜별 폴더 구조(YYYY/MM) 및 고도화된 저장 로직"""
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # 1. 언어별/날짜별 경로 설정 (구조적 관리)
    base_path = f"content/{lang}/posts/{year}/{month}"
    os.makedirs(base_path, exist_ok=True)
    
    # 2. 파일명 (영문 슬러그 공유)
    slug = sanitize_slug(article['eng_title'])
    timestamp = int(time.time())
    md_filename = f"{slug}-{timestamp}.md"
    
    # 3. 이미지 영구 저장 (V7.2)
    original_img = article.get('original_image_url')
    cat_slug = article.get('eng_category_slug', 'tech-biz')
    local_img_url = download_image(original_img, cat_slug, slug)
    
    # 4. 언어별 원고 구성
    cat_slug = article.get('eng_category_slug', 'tech-biz')
    tags = json.dumps(article.get('keywords', []), ensure_ascii=False)
    is_featured = "true" if article.get('score', 0) >= 9 else "false"
    
    if lang == 'ko':
        title = article['kor_title']
        summary_first_line = article.get('kor_summary', '').split('\n')[0][:100]
        content = f"""---
title: "{title}"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{summary_first_line}"
image: "{local_img_url}"
categories: ["{cat_slug}"]
tags: {tags}
featured: {is_featured}
---

## 📋 Executive Summary: 핵심 이슈 브리핑

{article.get('kor_summary', '내용 요약 중...')}

---

## 🔍 심층 분석: 글로벌 테크 리포트

{article.get('kor_content', '진행 중...')}

---

## 💡 Editorial: 미래 전략과 시장 전망

{article.get('kor_insight', '인사이트 분석 중...')}
"""
    else: # English
        title = article['eng_title']
        eng_desc = article.get('eng_content', '')[:150].replace('"', "'")
        content = f"""---
title: "{title}"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{eng_desc}..."
image: "{local_img_url}"
categories: ["{cat_slug}"]
tags: {tags}
featured: {is_featured}
---

{article.get('eng_content', 'Processing...')}

---
*Published by Lego-Sia Intelligence (V10.0)*
"""

    with open(f"{base_path}/{md_filename}", "w", encoding="utf-8-sig") as f:
        f.write(content)
    
    return md_filename

def save_raw_archive(article, slug):
    """API 원본 데이터를 배포되지 않는 별도 폴더에 JSON으로 영구 보관"""
    archive_dir = "automation/raw_archive"
    os.makedirs(archive_dir, exist_ok=True)
    
    archive_path = os.path.join(archive_dir, f"{slug}.json")
    try:
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f" [!] Raw archive save failed: {e}")

def main():
    print(f"=== [V10.7 Global] April 2026 Strategy Engine Starting ===")
    
    harvester = NewsHarvester()
    editor = NewsEditor()
    history = HistoryManager()
    reviewer = EditorInChief() 
    telegram = TelegramRemote() # [V10.8] 알림 봇 소환
    
    # 1. 뉴스 수집 (중복 기사 필터링 포함)
    raw_news = harvester.fetch_all(limit_per_cat=5)
    
    new_articles = []
    seen_titles = [] 
    published_urls = [] 
    
    # 2. 중복 처리 강화
    for article in raw_news:
        url = article['url']
        title = article['title']
        
        is_duplicate = False
        if history.is_already_processed(url) or history.is_similar_title_exists(title, threshold=0.5):
            is_duplicate = True
        
        for seen_title in seen_titles:
            if title[:15] == seen_title[:15]:
                is_duplicate = True
                break
        
        if not is_duplicate:
            new_articles.append(article)
            seen_titles.append(title)
    
    if not new_articles:
        print("[*] No unique news found. Archive is steady.")
        return

    # 3. AI 2-Step Editorial & Final AI Review
    print(f"[*] Council Meeting: Reviewing {len(new_articles)} candidates...")
    
    category_quota = {"tech-biz": 2, "monetization": 3}
    current_counts = {}

    sorted_articles = sorted(new_articles, key=lambda x: 0 if any(k in x['category'].lower() or k in x['title'].lower() for k in ["ai", "chip", "hardware", "game"]) else 1)
    
    for article in sorted_articles:
        drafts = editor.review_batch([article])
        for draft in drafts:
            cat_map = {"AI-기술": "ai-tech", "AI-에이전트": "ai-agents", "하드웨어": "hardware", "게임": "game", "수익화-전략": "monetization", "테크-비즈니스": "tech-biz"}
            cat_slug = cat_map.get(draft.get('category', 'tech-biz'), 'tech-biz')
            draft['eng_category_slug'] = cat_slug
            
            # [V10.7] AI 국장의 최종 심사
            review = reviewer.review_article(draft)
            if not review.get('approval', False):
                print(f" [REJECTED by Chief Editor] Score {review.get('score')}: {draft['kor_title'][:30]}")
                print(f"   Critique: {review.get('critique')}")
                continue

            # 쿼터제 적용
            count = current_counts.get(cat_slug, 0)
            if cat_slug in category_quota and count >= category_quota[cat_slug]:
                continue

            if draft.get('score', 0) >= 8:
                post_slug = sanitize_slug(draft['eng_title'])
                save_raw_archive(article, post_slug)
                
                now = datetime.now()
                url_path = f"posts/{now.strftime('%Y/%m')}/{post_slug}/"
                
                create_hugo_post(draft, lang='ko')
                create_hugo_post(draft, lang='en')
                
                published_urls.append(f"https://news.lego-sia.com/{url_path}")
                published_urls.append(f"https://news.lego-sia.com/en/{url_path}")
                
                history.add_to_history(article['url'], draft['kor_title'])
                current_counts[cat_slug] = count + 1 
                print(f" [PASSED & PUBLISHED] {draft['kor_title']}")

    # [V10.7] 자동 배포 및 메타데이터 동기화
    if published_urls:
        print("[*] Syncing to Global Cloud (GitHub/Vercel)...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"auto: daily tech intelligence update ({len(published_urls)//2} articles)"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print(" [SUCCESS] Deployed to Production.")
            
            # [V10.8] 텔레그램 알림 전송
            article_count = len(published_urls) // 2
            telegram.send_resp(f"🚀 **배포 완료: 총 {article_count}건의 새로운 전략적 인사이트가 추가되었습니다.**\n지금 바로 [Lego-Sia Magazine](https://news.lego-sia.com)에서 확인해보세요! 😊")
            
            # 배포 성공 후에만 색인 알림 전송
            notify_indexnow(published_urls)
        except Exception as e:
            print(f" [!] Deployment failed: {e}")
            telegram.send_resp(f"⚠️ **배포 실패 알림:**\n오류 내용: {e}")

    print(f"[*] Mission Accomplished. Next window: 1 hour.")

if __name__ == "__main__":
    main()
