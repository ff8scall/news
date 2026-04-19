import os
import json
import re
import time
import hashlib
import requests
import logging
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from harvester_v3 import HarvesterV3
from common_utils import send_telegram_report

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

# [V3.21] 전역 카운터 (기사별 고유 시간 부여용)
# 미래 날짜 문제를 방지하기 위해 1시간 전(-3600초)부터 시작
POST_TIME_OFFSET = -3600

class StateTracker:
    """[V9.5] Thread-Safe Job State & Article Cache Management: Ensures resumable & atomic operations"""
    def __init__(self, state_file="automation/job_state.json", cache_dir="automation/cache"):
        self.state_file = state_file
        self.cache_dir = cache_dir
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.state = self.load_state()

    def load_state(self):
        with self.lock:
            if os.path.exists(self.state_file):
                try:
                    with open(self.state_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {"guides": {}, "news": {}}
            return {"guides": {}, "news": {}}

    def save_state(self):
        with self.lock:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)

    def is_done(self, section, slug, lang):
        with self.lock:
            return lang in self.state.get(section, {}).get(slug, [])

    def mark_done(self, section, slug, lang):
        with self.lock:
            if section not in self.state: self.state[section] = {}
            if slug not in self.state[section]: self.state[section][slug] = []
            if lang not in self.state[section][slug]:
                self.state[section][slug].append(lang)
        self.save_state()
        
        # 만약 모든 목표 언어(en, ko)가 완료되면 캐시 삭제
        if self.is_done(section, slug, "en") and self.is_done(section, slug, "ko"):
            self.clear_cache(slug)

    def save_cache(self, slug, article_data):
        cache_path = os.path.join(self.cache_dir, f"{slug}.json")
        with self.lock:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, indent=4, ensure_ascii=False)
    
    def load_cache(self, slug):
        cache_path = os.path.join(self.cache_dir, f"{slug}.json")
        if os.path.exists(cache_path):
            with self.lock:
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return None
        return None

    def clear_cache(self, slug):
        cache_path = os.path.join(self.cache_dir, f"{slug}.json")
        if os.path.exists(cache_path):
            try: os.remove(cache_path)
            except: pass

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
    "models": "AI 모델", "apps": "AI 활용",
    "high-end": "하이엔드 PC", "chips": "반도체",
    "analysis": "비교·분석", "guide": "개발·팁"
}

# [V1.1] Alignment with actual fallback filenames in static/images/fallbacks/
# [V4.0] 초정예 폴백 이미지 매핑
FALLBACK_MAP = {
    "ai": "ai-tech",
    "hardware": "hardware",
    "insights": "guides",
    "models": "ai-models",
    "apps": "ai-tools",
    "high-end": "hardware",
    "chips": "semi-hbm",
    "analysis": "ai-tech",
    "guide": "ai-tech"
}

def download_image(url, category_slug, slug):
    """[V3.5] Article Image -> Return None if fail (to trigger AI generation)"""
    if not url or str(url).lower() == 'none' or not str(url).startswith('http'):
        return None
    
    # [V3.19] 가짜 이미지 링크(HTML 페이지 등) 필터링
    lower_url = url.lower().split('?')[0] # 쿼리 파라미터 제외하고 확장자 확인
    valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']
    if not any(ext in lower_url for ext in valid_exts) or 'html' in lower_url:
        logger.warning(f" [IMAGE] Skipping non-image URL: {url}")
        return None

    if url.startswith('//'): url = 'https:' + url
    
    date_dir = datetime.now().strftime('%Y/%m/%d')
    img_dir = f"static/images/posts/{date_dir}"
    os.makedirs(img_dir, exist_ok=True)
    
    img_path = f"{img_dir}/{slug}.jpg"
    web_url = f"/images/posts/{date_dir}/{slug}.jpg"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/123.0.0.0',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        resp = requests.get(url, timeout=(5, 15), headers=headers)
        if resp.status_code == 200:
            with open(img_path, 'wb') as f: f.write(resp.content)
            return web_url
        else:
            logger.warning(f" [IMAGE] Download failed with status {resp.status_code}: {url}")
    except Exception as e:
        logger.warning(f" [IMAGE] Download error ({url}): {e}")
    
    return None

def generate_and_save_thumbnail(image_prompt_core, slug_name, retries=2):
    """[V8.1] Pollinations.ai 이미지 생성 (재시도 포함)"""
    aesthetic_base = ", high-tech minimalism, cinematic 3D render, dark metallic texture, neon accents, isometric perspective, Unreal Engine 5 aesthetic, 8k resolution --no text, no faces, no humans"
    final_prompt = (image_prompt_core if image_prompt_core else "Abstract futuristic technology concept") + aesthetic_base
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
    
    for attempt in range(retries + 1):
        try:
            response = requests.get(image_url, timeout=45)
            if response.status_code == 200 and len(response.content) > 5000:
                date_dir = datetime.now().strftime("%Y/%m/%d")
                save_dir = f"static/images/posts/{date_dir}"
                os.makedirs(save_dir, exist_ok=True)
                save_path = f"{save_dir}/{slug_name}_gen.jpg"
                with open(save_path, 'wb') as f: f.write(response.content)
                return f"/images/posts/{date_dir}/{slug_name}_gen.jpg"
        except Exception:
            pass
        if attempt < retries:
            time.sleep(2)
    return None


def _format_readable_content(text):
    """[V8.1] 본문 텍스트의 가독성을 향상시키는 포매터.
    - 마크다운 헤더(##) 앞뒤에 빈 줄 보장
    - 긴 문단을 3~4문장 단위로 분할하여 빈 줄 삽입
    - 이미 잘 포맷된 텍스트는 건드리지 않음
    """
    if not text:
        return text
    
    lines = text.split('\n')
    formatted = []
    
    for line in lines:
        stripped = line.strip()
        
        # 빈 줄은 그대로 유지
        if not stripped:
            formatted.append('')
            continue
        
        # 마크다운 헤더 앞에 빈 줄 보장
        if stripped.startswith('#'):
            if formatted and formatted[-1] != '':
                formatted.append('')
            formatted.append(stripped)
            formatted.append('')
            continue
        
        # 리스트 아이템은 그대로
        if stripped.startswith('- ') or stripped.startswith('* ') or re.match(r'^\d+\.\s', stripped):
            formatted.append(stripped)
            continue
        
        # 긴 문단(200자 초과)은 문장 단위로 분할
        if len(stripped) > 200:
            sentences = re.split(r'(?<=[.!?다요음됩니다])\s+', stripped)
            chunk = []
            for sent in sentences:
                chunk.append(sent)
                if len(chunk) >= 3:
                    formatted.append(' '.join(chunk))
                    formatted.append('')
                    chunk = []
            if chunk:
                formatted.append(' '.join(chunk))
                formatted.append('')
        else:
            formatted.append(stripped)
            formatted.append('')
    
    # 연속된 빈 줄 제거 (최대 1개만)
    result = []
    for line in formatted:
        if line == '' and result and result[-1] == '':
            continue
        result.append(line)
    return '\n'.join(result).strip()

def is_already_published(slug):
    """[V4.4] 기사가 이미 발행되었는지 파일 시스템 전수 조사 (중복 방지용)"""
    base_dir = "content/ko/posts"
    if not os.path.exists(base_dir):
        return False
    
    # 해당 슬러그로 끝나는 .md 파일이 있는지 검색
    for root, dirs, files in os.walk(base_dir):
        if f"{slug}.md" in files:
            return True
    return False

def create_hugo_post(article, lang='ko'):
    global POST_TIME_OFFSET
    pub_date = datetime.now() + timedelta(seconds=POST_TIME_OFFSET)
    POST_TIME_OFFSET += 5  # [V4.3] 5초 간격으로 중복 방지 및 미래 시간 방지
    date_path = pub_date.strftime("%Y/%m/%d")
    target_dir = f"content/{lang}/posts/{date_path}"
    os.makedirs(target_dir, exist_ok=True)
    slug = article['sync_slug']
    cat_safe = sanitize_slug(article.get('category', 'ai-models'))
    
    # [V10.0] Tiered Image Strategy 통합
    from image_manager import get_tiered_image
    
    thumbnail_url = article.get('thumbnail_image')
    if not thumbnail_url:
        thumbnail_url = get_tiered_image(article, slug)
        article['thumbnail_image'] = thumbnail_url # 캐싱
    
    ai_img_url = article.get('_shared_image') or thumbnail_url
    
    filepath = os.path.join(target_dir, f"{slug}.md")
    
    # 본문에 AI 이미지 삽입 (썸네일과 다를 경우에만 혹은 항상)
    ai_img_md = ""
    if ai_img_url and ai_img_url != thumbnail_url:
        ai_img_md = f"\n\n![AI Insight Visualization]({ai_img_url})\n*<center>AI-generated visualization based on the depth analysis of this article.</center>*\n\n"

    if lang == 'ko':
        title = article.get('kor_title', '제목 없음')
        kor_sum = article.get('kor_summary', [])
        desc_val = article.get('kor_description', kor_sum[0] if kor_sum else title)
        tags_val = json.dumps(article.get('kor_keywords', []), ensure_ascii=False)
        date_str = pub_date.strftime('%Y-%m-%dT%H:%M:%S+09:00')
        analysis_title = article.get('kor_analysis_title', '상세 분석')
        insight_title = article.get('kor_insight_title', '인사이트 비평')
        summary_text = "\n".join([f"- {s}" for s in article.get('kor_summary', [])])
        formatted_content = _format_readable_content(article.get('kor_content', ''))
        formatted_insight = _format_readable_content(article.get('kor_insight', ''))
        
        content_body = f"## 핵심 요약\n{summary_text}\n\n"
        if formatted_content:
            content_body += f"## {analysis_title}\n{formatted_content}{ai_img_md}\n\n"
        if formatted_insight:
            content_body += f"## {insight_title}\n{formatted_insight}"
        content_body = content_body.strip()
    else:
        title = article.get('eng_title', 'Untitled')
        eng_desc = article.get('eng_description')
        desc_val = eng_desc if eng_desc else (article.get('eng_summary') if article.get('eng_summary') else title)
        tags_val = json.dumps(article.get('eng_keywords', []), ensure_ascii=False)
        from datetime import timezone
        date_str = pub_date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        summary_val = article.get('eng_summary', '')
        summary_section = f"## Executive Summary\n{summary_val}\n\n" if summary_val else ""
        formatted_eng_content = _format_readable_content(article.get('eng_content', 'Content not localized yet.'))
        content_body = f"{summary_section}## Strategic Deep-Dive\n{formatted_eng_content}{ai_img_md}"

    # [V3.1] Frontmatter Generation
    safe_title = title.replace('"', "'")
    safe_desc = desc_val.replace('"', "'")
    is_featured = "true" if article.get('featured') else "false"

    post_md = f"""---
title: "{safe_title}"
date: "{date_str}"
description: "{safe_desc}"
image: "{thumbnail_url}"
clusters: ["{article.get('cluster', 'ai-models-tools')}"]
categories: ["{cat_safe}"]
tags: {tags_val}
featured: {is_featured}
---
{content_body}
"""
    with open(filepath, "w", encoding="utf-8-sig") as f: f.write(post_md)
    return True

def process_category(cat, items, editor, tracker, use_local=False, limit=1):
    """[Helper] Thread-safe category processing worker - returns number of processed items"""
    if not items: return 0
    
    model_name = "gemma4:26b" if use_local else None
    processed_count = 0
    
    for item in items:
        if processed_count >= limit: break
        
        safe_slug = sanitize_slug(item['title'])
        # 이미 한 쪽이라도 되었거나 캐시가 있으면 진행 (둘 다 완료된 경우만 스킵)
        if tracker.is_done("news", safe_slug, "ko") and tracker.is_done("news", safe_slug, "en"): 
            continue

        try:
            start_time = time.time()
            logger.info(f"[PROCESS_START] [{cat}] Starting: {item['title'][:50]}")
            
            # Step 1: Article Data 취득 (캐시 우선 확인)
            article_data = tracker.load_cache(safe_slug)
            
            if not article_data:
                logger.info(f"[CACHE_MISS] No cache for {safe_slug}. Calling AI...")
                t0 = time.time()
                article_data_list = editor.review_batch([item], hint_category=cat, model=model_name if use_local else None)
                t1 = time.time()
                logger.info(f"[TIME] [{cat}] AI Content Generation took {t1-t0:.2f}s")
                
                if article_data_list:
                    article_data = article_data_list[0]
                    article_data['sync_slug'] = safe_slug
                    if 'category' not in article_data:
                        article_data['category'] = cat
                    # 캐시에 저장
                    tracker.save_cache(safe_slug, article_data)
                else:
                    logger.warning(f"[FAIL] AI Revision failed for {item['title']}")
                    continue
            else:
                logger.info(f"[CACHE_HIT] Resuming with cached data for {safe_slug}")

            # Step 2: English Post (미완료 시)
            if not tracker.is_done("news", safe_slug, "en"):
                t2 = time.time()
                create_hugo_post(article_data, lang='en')
                tracker.mark_done("news", safe_slug, "en")
                t3 = time.time()
                logger.info(f"[TIME] [{cat}] English Post Creation took {t3-t2:.2f}s")
            
            # Step 3: Korean Post (미완료 시)
            if not tracker.is_done("news", safe_slug, "ko"):
                t4 = time.time()
                create_hugo_post(article_data, lang='ko')
                tracker.mark_done("news", safe_slug, "ko")
                t5 = time.time()
                logger.info(f"[TIME] [{cat}] Korean Post Creation took {t5-t4:.2f}s")
                
            total_time = time.time() - start_time
            logger.info(f"[SUCCESS] [{cat}] Total Process Time: {total_time:.2f}s")
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to process {item['title']} in {cat}: {e}")
    return processed_count

def manage_news_pipeline(limit_per_cat=1, use_local=False):
    """[V10.1] Production News Pipeline: Batch support"""
    logger.info(f"[V4.6] Production Orchestrator: Local={use_local} mode")
    
    harvester = HarvesterV3()
    tracker = StateTracker()
    writer = AIWriter()
    editor = NewsEditor(writer=writer)
    
    # 더 많은 후보를 수확하여 선택 폭을 넓힘
    news_items, stats = harvester.fetch_all(limit_per_cat=limit_per_cat + 2)
    logger.info(f"Harvested: {stats}")
    
    items_by_cat = {}
    for item in news_items:
        cat = item['eng_category_slug']
        if cat not in items_by_cat: items_by_cat[cat] = []
        items_by_cat[cat].append(item)
    
    categories = ["models", "apps", "chips", "high-end", "analysis", "guide"]
    total_published = 0
    
    # 정기 배치는 안정성을 위해 순차 처리 (Throttling 준수)
    for cat in categories:
        count = process_category(cat, items_by_cat.get(cat, []), editor, tracker, use_local, limit=limit_per_cat)
        total_published += count

    summary_msg = f"✅ Production Pipeline Cycle Completed!\nSuccessfully Published: {total_published} articles."
    logger.info(summary_msg)
    return summary_msg

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--local", action="store_true", default=False) 
    parser.add_argument("--mode", type=str, default="legacy", choices=["legacy", "premium"],
                        help="Choose 'premium' to run the NotebookLM Mega-Trend Macro Synthesis.")
    args = parser.parse_args()
    
    if args.mode == "premium":
        logger.info("[MODE: PREMIUM] Redirecting to NotebookLM Synthesis Pipeline...")
        from notebooklm_prep import process_macro_synthesis
        process_macro_synthesis(limit_per_cat=args.limit)
        report = "Premium Pipeline Phase 1 (NotebookLM Sync) Completed Successfully."
    else:
        logger.info("[MODE: LEGACY] Starting standard daily pipeline...")
        report = manage_news_pipeline(limit_per_cat=args.limit, use_local=args.local)
        
    try:
        send_telegram_report(report)
    except Exception as e:
        logger.error(f"Telegram Fail: {e}")
    print(f"Pipeline finished.")

if __name__ == "__main__": 
    main()
