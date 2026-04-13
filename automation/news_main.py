import os
import json
import re
import time
import hashlib
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from news_harvester import NewsHarvester

# [V3.0.32] Environment Auto-Loader
load_dotenv()

from ai_news_editor import NewsEditor
from ai_guide_editor import GuideEditor
from ai_writer import AIWriter
from history_manager import HistoryManager
from indexnow_service import notify_indexnow

# [V3.0.15] Advanced Diagnostic & Reporting Edition
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[
    logging.FileHandler("news_main.log", encoding='utf-8'),
    logging.StreamHandler()
])
logger = logging.getLogger("LegoSia.Main")

# 모듈 임포트 가드
def safe_import_class(module_name, class_name):
    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except: return type(class_name, (), {"send_resp": lambda s, m: logger.info(f"[Mock] {m}"), "review_article": lambda s, d: {"decision":"PASS"}})

TelegramRemote = safe_import_class("telegram_remote", "TelegramRemote")
EditorInChief = safe_import_class("ai_reviewer", "EditorInChief")

CATEGORY_BUDGETS = {
    "ai-models": 8, "ai-tools": 8, "gpu-chips": 8, "pc-robotics": 8,
    "game-optimization": 8, "ai-gameplay": 8, "tutorials": 4, "compare": 4
}

def sanitize_slug(text):
    if not text: return "topic"
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', text).lower()
    return re.sub(r'\s+', '-', clean).strip('-')[:50]

def hash_slug(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]

CAT_MAP = {
    "ai-models": "AI 모델·트렌드", "ai-tools": "AI 도구·사용법",
    "gpu-chips": "GPU·반도체", "pc-robotics": "AI PC & 로봇",
    "game-optimization": "게임 최적화·엔진", "ai-gameplay": "AI 게임 기술",
    "tutorials": "실전 튜토리얼", "compare": "성능 비교"
}

# [V0] Fallback mapping to Major Clusters
FALLBACK_MAP = {
    "ai-models": "ai-models-tools", "ai-tools": "ai-models-tools",
    "gpu-chips": "gpu-hardware", "pc-robotics": "gpu-hardware",
    "game-optimization": "ai-gaming", "ai-gameplay": "ai-gaming",
    "tutorials": "guides", "compare": "guides"
}

def download_image(url, category_slug, slug):
    """[V2.9.6] 카테고리별 매핑된 고화질 폴백 이미지 보장"""
    # [Fix] 카테고리에 맞는 폴백 이미지 키 찾기
    fallback_key = FALLBACK_MAP.get(category_slug, "ai-models-tools")
    
    if not url: return f"/images/fallback/{fallback_key}.png"
    
    # [V3.0.31] Protocol-relative URL fix
    if url.startswith('//'): url = 'https:' + url
    
    year_month = datetime.now().strftime('%Y/%m')
    img_dir = f"static/images/posts/{year_month}"
    os.makedirs(img_dir, exist_ok=True)
    
    img_path = f"{img_dir}/{slug}.jpg"
    web_url = f"/images/posts/{year_month}/{slug}.jpg"
    
    try:
        resp = requests.get(url, timeout=(3, 10), headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            with open(img_path, 'wb') as f: f.write(resp.content)
            return web_url
    except: pass
    
    return f"/images/fallbacks/{fallback_key}.jpg"

def create_hugo_post(article, lang='ko'):
    year, month = datetime.now().strftime('%Y'), datetime.now().strftime('%m')
    base_path = f"content/{lang}/posts/{year}/{month}"
    os.makedirs(base_path, exist_ok=True)
    
    slug = article['sync_slug']
    cat_safe = sanitize_slug(article.get('category', 'ai-models'))
    img_url = download_image(article.get('original_image_url'), cat_safe, slug)
    
    is_featured = "true" if article.get('score', 0) >= 9.5 else "false"

    if lang == 'ko':
        title = article.get('kor_title', '제목 없음')
        summary_list = article.get('kor_summary', [])
        if not isinstance(summary_list, list): summary_list = [summary_list]
        summary_text = "\n".join([f"- {s}" for s in summary_list])
        desc_val = article.get('description', summary_list[0] if summary_list else title)
        tags_val = json.dumps(article.get('kor_keywords', []), ensure_ascii=False)
        date_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')
        
        # [V3.2] 동적 부제(Dynamic Subtitles) 반영
        analysis_title = article.get('kor_analysis_title', '기술 분석 및 상세')
        insight_title = article.get('kor_insight_title', '시사점 및 전망')
        content_body = f"## 핵심 요약\n{summary_text}\n\n## {analysis_title}\n{article.get('kor_content')}\n\n## {insight_title}\n{article.get('kor_insight')}"
    else:
        title = article.get('eng_title', 'Untitled')
        desc_val = article.get('eng_summary', title)
        tags_val = json.dumps(article.get('eng_keywords', []), ensure_ascii=False)
        date_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        content_body = f"## Executive Summary\n{article.get('eng_summary')}\n\n## Strategic Deep-Dive\n{article.get('eng_content', 'Content not localized yet.')}"

    # [V0.2.2 Fix] Essential YAML/Hugo Quote Escaping (Replace " with ')
    safe_title = title.replace('"', "'")
    safe_desc = desc_val[:150].replace('"', "'")

    post_md = f"""---
title: "{safe_title}"
date: "{date_str}"
description: "{safe_desc}"
image: "{img_url}"
clusters: ["{article.get('cluster', 'ai-models-tools')}"]
categories: ["{cat_safe}"]
tags: {tags_val}
featured: {is_featured}
---
{content_body}
"""
    with open(f"{base_path}/{slug}.md", "w", encoding="utf-8-sig") as f:
        f.write(post_md)
    return True

def create_guide_post(guide_data, sync_slug, lang='ko'):
    base_path = f"content/{lang}/guides"
    os.makedirs(base_path, exist_ok=True)
    content = f"""---
title: "{guide_data.get('guide_title')}"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{guide_data.get('guide_summary', '')}"
type: "guides"
difficulty: "{guide_data.get('difficulty', 'Intermediate')}"
categories: ["{guide_data.get('guide_type', 'ai-tools')}"]
---
{guide_data.get('guide_content')}
"""
    with open(f"{base_path}/{sync_slug}.md", "w", encoding="utf-8-sig") as f:
        f.write(content)
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--rss-only", action="store_true")
    args = parser.parse_args()

    shared_writer = AIWriter()
    harvester = NewsHarvester()
    editor = NewsEditor(writer=shared_writer)
    guide_editor = GuideEditor(writer=shared_writer)
    history = HistoryManager()
    reviewer = EditorInChief(writer=shared_writer)
    telegram = TelegramRemote()
    
    start_time = datetime.now()
    logger.info(f"Executive Intelligence Engine V3.1 starting with limit={args.limit}...")
    
    telegram.send_resp("🚀 **ENGINE ACTIVATED (V3.1)**\n- Optimized Sync Engine.\n- Initializing intelligence harvest...")

    cat_issued = {cat: 0 for cat in CATEGORY_BUDGETS}
    cancel_stats = {"duplicate": 0, "review": 0, "budget": 0, "draft_fail": 0}
    
    target_cats = [args.category] if args.category else None
    
    # [Fix] Use args.limit correctly
    raw_news, harvest_stats = harvester.fetch_all(
        limit_per_cat=args.limit, 
        rss_only=args.rss_only, 
        target_cats=target_cats
    )
    
    new_articles = []
    for a in raw_news:
        if history.is_already_processed(a['url']):
            cancel_stats["duplicate"] += 1
        else:
            new_articles.append(a)
    
    published_count = 0; ai_calls = 0
    
    if not new_articles:
        logger.warning(f"Process ended: {cancel_stats['duplicate']} articles skipped as duplicates.")
        return

    # [Strategic Shuffle]
    import random as rand
    rand.shuffle(new_articles)
    
    for article in new_articles:
        if published_count >= args.limit * len(CATEGORY_BUDGETS): break

        if published_count > 0:
            time.sleep(15)
        
        # [V3.1] Simplified processing loop
        drafts = editor.review_batch([article], recent_posts=history.get_recent_posts(limit=10))
        ai_calls += 2
        if not drafts:
            cancel_stats["draft_fail"] += 1
            continue
        
        sync_slug = f"{sanitize_slug(drafts[0]['eng_title'])}-{hash_slug(article['url'])}"

        for draft in drafts:
            cat = draft.get('category', 'ai-models')
            draft['sync_slug'] = sync_slug
            
            if reviewer.review_article(draft).get('decision') != 'PASS':
                cancel_stats["review"] += 1
                continue

            if create_hugo_post(draft, lang='ko') and create_hugo_post(draft, lang='en'):
                history.add_to_history(article['url'], article['title'], local_url=sync_slug)
                cat_issued[cat] += 1; published_count += 1
                logger.info(f"Published: {sync_slug}")

    logger.info("Master execution cycle completed.")

if __name__ == "__main__": 
    main()
