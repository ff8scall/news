import os
import json
import re
import time
import hashlib
import requests
import logging
from datetime import datetime
from difflib import SequenceMatcher
from news_harvester import NewsHarvester
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
    "llm-tech": 6, "ai-agent": 6, "ai-policy": 3, "future-sw": 5,
    "semi-hbm": 6, "hpc-infra": 5, "robotics": 3,
    "monetization": 4, "startups-vc": 5, "market-trend": 3,
    "game-tech": 4, "spatial-tech": 5
}

def sanitize_slug(text):
    if not text: return "topic"
    clean = re.sub(r'[^a-zA-Z0-9\s-]', '', text).lower()
    return re.sub(r'\s+', '-', clean).strip('-')[:50]

def hash_slug(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]

CAT_MAP = {
    "llm-tech": "LLM·생성AI", "ai-agent": "AI 에이전트", "ai-policy": "AI 규제/정책", "future-sw": "미래 SW/개발",
    "semi-hbm": "차세대 반도체", "hpc-infra": "HPC/인프라", "robotics": "로보틱스",
    "monetization": "수익화 전략", "startups-vc": "비지니스/VC", "market-trend": "시장 트렌드",
    "game-tech": "게임 테크", "spatial-tech": "공간 컴퓨팅"
}

FALLBACK_MAP = {
    "llm-tech": "llm-tech",
    "ai-agent": "ai-agent",
    "ai-policy": "ai-policy",
    "future-sw": "future-sw",
    "semi-hbm": "semi-hbm",
    "hpc-infra": "hpc-infra",
    "robotics": "robotics",
    "monetization": "monetization",
    "startups-vc": "startups-vc",
    "market-trend": "market-trend",
    "game-tech": "game-tech",
    "spatial-tech": "spatial-tech"
}

def download_image(url, category_slug, slug):
    """[V2.9.6] 카테고리별 매핑된 고화질 폴백 이미지 보장"""
    # [Fix] 카테고리에 맞는 폴백 이미지 키 찾기
    fallback_key = FALLBACK_MAP.get(category_slug, "tech-biz")
    
    if not url: return f"/images/fallbacks/{fallback_key}.jpg"
    
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
    cat_safe = sanitize_slug(article.get('category', 'ai-tools'))
    img_url = download_image(article.get('original_image_url'), cat_safe, slug)
    
    is_featured = "true" if article.get('score', 0) >= 9.5 else "false"

    if lang == 'ko':
        title = article.get('kor_title', '제목 없음')
        summary_list = article.get('kor_summary', [])
        tags = json.dumps(article.get('kor_keywords', []), ensure_ascii=False)
        if not isinstance(summary_list, list): summary_list = [summary_list]
        summary_text = "\n".join([f"- {s}" for s in summary_list])
        desc = summary_list[0] if summary_list else ""
        
        # [V3.2] 동적 부제(Dynamic Subtitles) 반영: SEO 키워드 노출 극대화
        analysis_title = article.get('kor_analysis_title', '기술 분석 및 상세')
        insight_title = article.get('kor_insight_title', '시사점 및 전망')
        content_body = f"## 핵심 요약\n{summary_text}\n\n## {analysis_title}\n{article.get('kor_content')}\n\n## {insight_title}\n{article.get('kor_insight')}"
    else:
        title = article.get('eng_title', 'Untitled')
        desc = article.get('eng_summary', '')
        tags = json.dumps(article.get('eng_keywords', []), ensure_ascii=False)
        
        # [V3.2] English Consistency: Use dynamic headers if possible, otherwise fallback
        content_body = f"## Executive Summary\n{article.get('eng_summary')}\n\n## Strategic Deep-Dive\n{article.get('eng_content', 'Content not localized yet.')}"

    post_md = f"""---
title: "{title}"
date: "{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}"
description: "{desc[:150]}"
image: "{img_url}"
clusters: ["{article.get('cluster', 'Intelligence')}"]
categories: ["{cat_safe}"]
tags: {tags}
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
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--rss-only", action="store_true")
    args = parser.parse_args()

    # [V3.0.30] Shared AI Logic: All components now share a single throttled writer
    shared_writer = AIWriter()
    harvester = NewsHarvester()
    editor = NewsEditor(writer=shared_writer)
    guide_editor = GuideEditor(writer=shared_writer)
    history = HistoryManager()
    reviewer = EditorInChief(writer=shared_writer)
    telegram = TelegramRemote()
    
    start_time = datetime.now()
    logger.info("Executive Intelligence Engine V3.0.30 starting with Shared Throttled Writer...")
    
    # [V3.0.30] Initial Pulse: Ensure Telegram is reachable
    telegram.send_resp("🚀 **ENGINE ACTIVATED (V3.0.30)**\n- Shared Throttled AI Writer online.\n- Initializing intelligence harvest...")

    cat_issued = {cat: 0 for cat in CATEGORY_BUDGETS}
    cancel_stats = {"duplicate": 0, "review": 0, "budget": 0, "draft_fail": 0}
    
    target_cats = [args.category] if args.category else None
    raw_news, harvest_stats = harvester.fetch_all(
        limit_per_cat=args.limit, 
        rss_only=args.rss_only, 
        target_cats=target_cats
    )
    
    new_articles = []
    for a in raw_news:
        if history.is_already_processed(a['url']):
            cancel_stats["duplicate"] += 1
            logger.info(f"Skipped (Duplicate): {a['title'][:50]}")
        else:
            new_articles.append(a)
    
    published_count = 0; published_guides = 0; ai_calls = 0
    published_urls = []
    
    if not new_articles:
        logger.warning(f"Process ended: {cancel_stats['duplicate']} articles skipped as duplicates.")
        report = f"✅ **INTELLIGENCE SCAN COMPLETE**\n\n- 소스 발견: {len(raw_news)}건\n- 중복 제외: {cancel_stats['duplicate']}건\n- 새로운 정보 없음 (0건 발행)"
        telegram.send_resp(report)
        return

    article_groups = [[a] for a in new_articles]
    # [V3.0.25] 공평성 강화: 대량 범주(future-sw 등)가 다른 희소 범주를 밀어내지 않도록 전체 셔플
    import random as rand
    rand.shuffle(article_groups)
    
    scored_groups = sorted([(9.0, g) for g in article_groups], key=lambda x: x[0], reverse=True)

    for score, group in scored_groups:
        limit_threshold = args.limit if args.category else 35
        if published_count >= limit_threshold:
            cancel_stats["budget"] += (len(scored_groups) - published_count)
            logger.info(f"Stopped: Budget reached ({limit_threshold})")
            break

        # [V3.0.23] 15초 인터그리티 펄스: API 할당량 보호 및 집필 품질 보장 (Throttling)
        if published_count > 0:
            logger.info("Throttling for API integrity (15s wait)...")
            time.sleep(15)
        
        # [V3.0.30] Intelligent Circuit Breaker: Trigger only if essential core providers are down
        if shared_writer.is_all_exhausted():
            logger.error("CRITICAL: Essential AI providers (Gemini, GitHub, Groq) exhausted. Triggering Circuit Breaker.")
            telegram.send_resp("⚠️ **CIRCUIT BREAKER TRIGGERED**\n- 핵심 AI (Gemini, GitHub) 할당량이 모두 소진되었습니다.\n- 남은 기사들은 다음 기동 시 재시도됩니다.")
            break

        # [V3.0.25] 가이드 트리거 확장: 벤치마크, 로드맵, 비교 분석 등 심층 분석 키워드 추가
        guide_triggers = ['how to', '설치', '방법', 'optimize', 'benchmark', 'comparison', 'roadmap', 'tutorial', 'analysis', 'guide']
        is_guide = score >= 8.5 and any(k in group[0]['title'].lower() for k in guide_triggers)
        
        drafts = editor.review_batch(group, recent_posts=history.get_recent_posts(limit=10))
        ai_calls += 2
        if not drafts:
            cancel_stats["draft_fail"] += 1
            logger.warning(f"Cancelled (Draft Fail): {group[0]['title'][:50]}")
            continue
        
        sync_slug = f"{sanitize_slug(drafts[0]['eng_title'])}-{hash_slug(group[0]['url'])}"

        for draft in drafts:
            cat = draft.get('category', 'ai-tools')
            if cat not in CATEGORY_BUDGETS: cat = 'ai-tools' 
            
            draft['sync_slug'], draft['score'] = sync_slug, score
            if reviewer.review_article(draft).get('decision') != 'PASS':
                cancel_stats["review"] += 1
                logger.warning(f"Cancelled (Review Low Score): {sync_slug}")
                continue

            year_month = datetime.now().strftime('%Y/%m')
            local_url = f"/posts/{year_month}/{sync_slug}/"

            if create_hugo_post(draft, lang='ko') and create_hugo_post(draft, lang='en'):
                for a in group: history.add_to_history(a['url'], a['title'], local_url=local_url)
                cat_issued[cat] += 1; published_count += 1
                
                full_url = f"https://news.lego-sia.com{local_url}"
                published_urls.append(full_url)
                logger.info(f"Published: {sync_slug} ({cat}) -> {local_url}")
                
                # [V3.0.25] 가이드 트리거 정밀화: AI가 매긴 실제 점수와 키워드 결합
                guide_triggers = ['how to', '설치', '방법', 'optimize', 'benchmark', 'comparison', 'roadmap', 'tutorial', 'analysis', 'guide']
                is_guide = score >= 8.5 and any(k in draft.get('kor_title', '').lower() for k in guide_triggers)
                
                if is_guide and published_guides < 3:
                    logger.info(f"Writing Strategic Guide for: {sync_slug}")
                    g_ko = guide_editor.write_guide(draft, lang='ko')
                    g_en = guide_editor.write_guide(draft, lang='en')
                    ai_calls += 2
                    if g_ko: 
                        create_guide_post(g_ko, sync_slug, lang='ko')
                        logger.info(f" -> KO Guide Published: {sync_slug}")
                    if g_en: 
                        create_guide_post(g_en, sync_slug, lang='en')
                        logger.info(f" -> EN Guide Published: {sync_slug}")
                    published_guides += 1

    # [V3.0.15 Strategic Report]
    duration = (datetime.now() - start_time).seconds
    quota_info = "\n".join([f"- {k}: {v}건" for k, v in harvest_stats.items() if v > 0])
    
    cancel_breakdown = f"""• 중복 기사: {cancel_stats['duplicate']}건
• 리뷰 낙폭: {cancel_stats['review']}건
• 예산 초과: {cancel_stats['budget']}건
• 초안 실패: {cancel_stats['draft_fail']}건"""

    # [V3.0.26] 발행 카테고리 상세 내역 추가
    pub_list = "\n".join([f"- {CAT_MAP.get(k, k)}: {v}건" for k, v in cat_issued.items() if v > 0])
    
    report = f"""✅ **STRATEGIC REPORT COMPLETE**

📦 **수집/발행 통계**
{quota_info}
---
**🚀 최종 발행 내역**
{pub_list}

📑 후보군: {len(raw_news)}건 -> 필터링: {published_count + sum(cancel_stats.values())}건

🚫 **취소 및 필터링 내역 (128/126 미스터리)**
{cancel_breakdown}

🤖 **AI 작업 통계**
- Gemini Calls: {ai_calls}회
- 성공률: {(published_count/len(new_articles)*100 if new_articles else 0):.1f}%

🚀 **발행 결과**
- 최종 발행: {published_count}건 (가이드: {published_guides}건)
- 소요 시간: {duration}초
    """
    telegram.send_resp(report)
    logger.info("Master execution cycle completed.")

if __name__ == "__main__": main()
