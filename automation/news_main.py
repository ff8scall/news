# -*- coding: utf-8 -*-
import os
import time
import sys
import json
import re
import glob
import random
from datetime import datetime

# [V12.0] 터미널 인코딩 및 출력 플러싱 최적화
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

from news_harvester import NewsHarvester
from ai_news_editor import NewsEditor
from history_manager import HistoryManager
from indexnow_service import notify_indexnow
from ai_reviewer import EditorInChief
from telegram_remote import TelegramRemote

import requests
import subprocess

def download_image(original_url, category_slug, slug):
    save_path = os.path.join("static", "images", f"{slug}.jpg")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if original_url and original_url.startswith("http"):
        try:
            print(f" [*] Attempting to download original image: {original_url[:50]}...")
            response = requests.get(original_url, timeout=12)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return f"/images/{slug}.jpg"
        except Exception as e:
            print(f" [!] Original image download failed: {e}")
    fallback_path = f"static/images/fallbacks/{category_slug}.jpg"
    if os.path.exists(fallback_path): return f"/images/fallbacks/{category_slug}.jpg"
    return "/images/fallback-default.jpg"

def sanitize_slug(title):
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', title).lower()
    return re.sub(r'\s+', '-', clean).strip('-')[:50]

def create_hugo_post(article, lang='ko'):
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    base_path = f"content/{lang}/posts/{year}/{month}"
    os.makedirs(base_path, exist_ok=True)
    slug = sanitize_slug(article['eng_title'])
    timestamp = int(time.time())
    md_filename = f"{slug}-{timestamp}.md"
    # [V12.1] 이미지 URL 추출 로직 강화 (다중 변수 체크)
    raw_img_url = article.get('original_image_url') or article.get('urlToImage') or article.get('image')
    local_img_url = download_image(raw_img_url, article.get('eng_category_slug', 'tech-biz'), slug)
    cat_slug = article.get('eng_category_slug', 'tech-biz')
    tags = json.dumps(article.get('keywords', []), ensure_ascii=False)
    is_featured = "true" if article.get('score', 0) >= 9 else "false"
    
    if lang == 'ko':
        title = article['kor_title']
        summary = article.get('kor_summary', '').split('\n')[0][:100]
        content = f"""---
title: "{title}"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{summary}"
image: "{local_img_url}"
categories: ["{cat_slug}"]
tags: {tags}
featured: {is_featured}
---

## Executive Summary: 핵심 이슈 브리핑

{article.get('kor_summary', '내용 요약 중...')}

---

## Deep Analysis: 글로벌 테크 리포트

{article.get('kor_content', '진행 중...')}

---

## Editorial Outlook: 미래 전략과 시장 전망

{article.get('kor_insight', '인사이트 분석 중...')}
"""
    else:
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
*Published by Lego-Sia Intelligence (V12.0)*
"""
    with open(f"{base_path}/{md_filename}", "w", encoding="utf-8-sig") as f:
        f.write(content)
    return md_filename

def get_api_quotas():
    results = []
    keys = {"NEWSAPI_ORG_KEY": "NewsAPI", "THENEWSAPI_KEY": "TheNewsAPI", "CURRENTSAPI_KEY": "CurrentsAPI", "GNEWS_API_KEY": "GNews"}
    for k, name in keys.items():
        v = os.getenv(k)
        if v:
            try:
                if name == "NewsAPI": res = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&pageSize=1&apiKey={v}", timeout=5)
                elif name == "TheNewsAPI": res = requests.get(f"https://api.thenewsapi.com/v1/news/top?api_token={v}&limit=1", timeout=5)
                elif name == "GNews": res = requests.get(f"https://gnews.io/api/v4/top-headlines?token={v}&max=1", timeout=5)
                else: res = requests.get(f"https://api.currentsapi.services/v1/latest-news?apiKey={v}", timeout=5)
                rem = res.headers.get('X-Remaining-Quota') or res.headers.get('X-RateLimit-Remaining') or "OK"
                results.append(f"- {name}: {rem}")
            except: pass
    return "\n".join(results) if results else "No quota data available."

def main():
    print(f"=== [V12.0 Hawk-Eye] Strategic Media Engine Initializing ===")
    harvester = NewsHarvester()
    from ai_writer import AIWriter
    writer = AIWriter()
    editor = NewsEditor(writer=writer)
    history = HistoryManager()
    reviewer = EditorInChief(writer=writer) 
    telegram = TelegramRemote()
    
    raw_news, harvest_stats = harvester.fetch_all(limit_per_cat=8) 
    new_articles = []
    seen_urls = set()

    for article in raw_news:
        url = article['url']
        title = article['title']
        if not history.is_already_processed(url) and not history.is_similar_title_exists(title):
            if url not in seen_urls:
                new_articles.append(article)
                seen_urls.add(url)
        else:
            # 테스트를 위해 중복/유사 기사 발견 시 로그 출력
            print(f" [SKIP] Duplicate or similar found: {title[:30]}...")

    # [테스트 전용] 중복이더라도 강제로 2건의 후보군을 포함시켜 로직 검증
    if not new_articles and len(raw_news) > 0:
        print("[!] TEST MODE: Forcing 2 candidates from raw pool to verify 6:2:2 logic.")
        new_articles = raw_news[:2]
    
    if not new_articles:
        print("[*] No unique news found. System on standby.")
        quota_report = get_api_quotas()
        telegram.send_resp(f"ℹ️ [SKIP] 새로운 뉴스가 없습니다.\n\n[수집통계]\n{json.dumps(harvest_stats, indent=2)}\n\n[QUOTA]\n{quota_report}")
        return

    # [V12.0 Unchained Mode] 발행 건수 제한 완전 제거. 쿼터가 허용하는 한 수집된 모든 양질의 뉴스 발행.
    published_count = 0
    published_urls = []

    # AI/전략 기사 우선 정렬
    sorted_candidates = sorted(new_articles, key=lambda x: 0 if any(k in x['title'].lower() for k in ["ai", "chip", "nvidia", "hardware", "semiconductor", "agent", "robot", "llm"]) else 1)

    for article in sorted_candidates:
        # 건수 제한 없이 모든 후보군 전수 조사
        
        if writer.is_all_exhausted():
            print(" [CRITICAL] All AI Providers exhausted. Capacity reached for this session.")
            break

        drafts = editor.review_batch([article])
        if not drafts: continue
        
        for draft in drafts:
            raw_cat = draft.get('category', 'tech-biz')
            cat_map = {
                "ai-tech": "ai-tech", "AI-기술": "ai-tech",
                "ai-agents": "ai-agents", "AI-에이전트": "ai-agents",
                "hardware": "hardware", "하드웨어": "hardware",
                "game": "gaming", "게임": "gaming",
                "monetization": "monetization", "수익화-전략": "monetization",
                "tech-biz": "tech-biz", "테크-비즈니스": "tech-biz"
            }
            cat_slug = cat_map.get(raw_cat, "tech-biz")
            draft['eng_category_slug'] = cat_slug
            
            # [V12.0 Aggressive Mode] 카테고리별 티켓 체크 제거 - 점수(Score)가 높으면 무조건 발행
            review = reviewer.review_article(draft)
            if review.get('decision') != 'PASS':
                print(f" [REJECTED] {draft['kor_title'][:30]} - Reason: {review.get('reason', 'Low Score')}")
                continue

            if draft.get('score', 0) >= 7:
                post_slug = sanitize_slug(draft['eng_title'])
                url_path = f"posts/{datetime.now().strftime('%Y/%m')}/{post_slug}/"
                create_hugo_post(draft, lang='ko')
                create_hugo_post(draft, lang='en')
                published_urls.append(f"https://news.lego-sia.com/{url_path}")
                published_urls.append(f"https://news.lego-sia.com/en/{url_path}")
                history.add_to_history(article['url'], draft['kor_title'])
                published_count += 1
                print(f" [PUB] {draft['kor_title']} (Score: {draft.get('score')})")
            else:
                print(f" DEBUG: Score too low ({draft.get('score')}) for final publication.")

    # [V11.8] 기사 발행 여부와 상관없이 항상 상태 보고 수행
    print(f"[*] Dispatching final intelligence report... (Articles: {published_count})")
    try:
        quota_report = get_api_quotas()
        
        # 상세 리포트 구성
        h_detail = "\n".join([f"- {k}: {v}건" for k, v in harvest_stats.items()])
        total_h = sum(harvest_stats.values())
        
        if published_count > 0:
            report_msg = f"✅ [STRATEGIC REPORT COMPLETE]\n\n" \
                         f"📦 [수집 통계]\n{h_detail}\n" \
                         f"📑 후보군: {total_h}건 -> 필터링: {len(new_articles)}건\n\n" \
                         f"🚀 [발행 규모]\n최종 발행: {published_count}건\n" \
                         f"성공률: {int(published_count/len(new_articles)*100)}%\n\n" \
                         f"[QUOTA]\n{quota_report}"
        else:
            report_msg = f"ℹ️ [SKIP] 새로운 뉴스가 없습니다.\n\n📦 [수집 통계]\n{h_detail}\n\n[QUOTA]\n{quota_report}"
            
        telegram.send_resp(report_msg)
        
        # 기사가 있을 때만 IndexNow 통보
        if published_urls:
            pass # notify_indexnow(published_urls)
            
    except Exception as e:
        print(f" [!] Report failed: {e}")

if __name__ == "__main__":
    telegram = TelegramRemote()
    try:
        # 1. 시작 알림
        telegram.send_resp("🚀 [Lego-Sia v12.0] Strategic News Engine 가동을 시작합니다.")
        main()
    except Exception as e:
        # 2. 에러 긴급 보고
        import traceback
        err_detail = traceback.format_exc()
        error_msg = f"⚠️ [CRITICAL ERROR] 엔진 가동 중단!\n\n원인: {str(e)}\n\n세부사항:\n{err_detail[:300]}..."
        print(error_msg)
        telegram.send_resp(error_msg)
        sys.exit(1)
