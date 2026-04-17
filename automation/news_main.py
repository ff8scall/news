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
    "ai-models": "AI 모델·트렌드", "ai-tools": "AI 도구·사용법",
    "gpu-chips": "GPU·반도체", "pc-robotics": "AI PC & 로봇",
    "game-optimization": "게임 최적화·엔진", "ai-gameplay": "AI 게임 기술",
    "tutorials": "실전 튜토리얼", "compare": "성능 비교"
}

# [V1.1] Alignment with actual fallback filenames in static/images/fallbacks/
FALLBACK_MAP = {
    "ai-models": "ai-models",
    "ai-tools": "ai-tools",
    "gpu-chips": "semi-hbm",
    "pc-robotics": "robotics",
    "game-optimization": "game-tech",
    "ai-gameplay": "gaming",
    "tutorials": "ai-tech",
    "compare": "ai-tech"
}

def download_image(url, category_slug, slug):
    """[V3.5] Article Image -> Return None if fail (to trigger AI generation)"""
    if not url: return None
    if url.startswith('//'): url = 'https:' + url
    
    date_dir = datetime.now().strftime('%Y/%m/%d')
    img_dir = f"static/images/posts/{date_dir}"
    os.makedirs(img_dir, exist_ok=True)
    
    img_path = f"{img_dir}/{slug}.jpg"
    web_url = f"/images/posts/{date_dir}/{slug}.jpg"
    
    try:
        resp = requests.get(url, timeout=(3, 10), headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            with open(img_path, 'wb') as f: f.write(resp.content)
            return web_url
    except Exception as e:
        logger.warning(f"[IMAGE] Download fail ({url}): {e}")
    
    return None

def generate_and_save_thumbnail(image_prompt_core, slug_name, retries=2):
    """[V8.1] Pollinations.ai 이미지 생성 (재시도 포함)"""
    aesthetic_base = ", high-tech minimalism, cinematic 3D render, dark metallic texture, neon accents, isometric perspective, Unreal Engine 5 aesthetic, 8k resolution --no text, no faces, no humans"
    final_prompt = (image_prompt_core if image_prompt_core else "Abstract futuristic technology concept") + aesthetic_base
    logger.info(f"[IMAGE] Creating thumbnail for {slug_name}")
    
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
            else:
                logger.warning(f"[IMAGE] Bad response (attempt {attempt+1}/{retries+1}): status={response.status_code}, size={len(response.content)}")
        except Exception as e:
            logger.warning(f"[IMAGE] Attempt {attempt+1}/{retries+1} failed: {e}")
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

def create_hugo_post(article, lang='ko'):
    date_path = datetime.now().strftime("%Y/%m/%d")
    target_dir = f"content/{lang}/posts/{date_path}"
    os.makedirs(target_dir, exist_ok=True)
    slug = article['sync_slug']
    cat_safe = sanitize_slug(article.get('category', 'ai-models'))
    
    # [V8.1] 이미지: _shared_image가 있으면 재생성 없이 바로 사용 (한/영 공유)
    img_url = article.get('_shared_image')
    
    if not img_url:
        # 기존 Triple-Layer Fallback: 1. Article Image, 2. AI Generated, 3. Category Default
        img_url = download_image(article.get('original_image_url'), cat_safe, slug)
        
        if not img_url:
            img_url = generate_and_save_thumbnail(article.get('image_prompt_core'), slug)
            if img_url:
                logger.info(f"[IMAGE] Using AI Generated image for {slug}")
            else:
                fallback_key = FALLBACK_MAP.get(cat_safe, "ai-tech")
                img_url = f"/images/fallbacks/{fallback_key}.jpg"
                logger.info(f"[IMAGE] Using Category Level-3 fallback for {slug}")
    
    filepath = os.path.join(target_dir, f"{slug}.md")
    if lang == 'ko':
        title = article.get('kor_title', '제목 없음')
        desc_val = article.get('kor_description', article.get('kor_summary', [title])[0])
        tags_val = json.dumps(article.get('kor_keywords', []), ensure_ascii=False)
        date_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')
        analysis_title = article.get('kor_analysis_title', '상세 분석')
        insight_title = article.get('kor_insight_title', '인사이트 비평')
        summary_text = "\n".join([f"- {s}" for s in article.get('kor_summary', [])])
        formatted_content = _format_readable_content(article.get('kor_content', ''))
        formatted_insight = _format_readable_content(article.get('kor_insight', ''))
        content_body = f"## 핵심 요약\n{summary_text}\n\n## {analysis_title}\n{formatted_content}\n\n## {insight_title}\n{formatted_insight}"
    else:
        title = article.get('eng_title', 'Untitled')
        eng_desc = article.get('eng_description')
        desc_val = eng_desc if eng_desc else (article.get('eng_summary') if article.get('eng_summary') else title)
        tags_val = json.dumps(article.get('eng_keywords', []), ensure_ascii=False)
        # Fix: Use local time with offset or UTC time correctly. 
        # Here we use +00:00 or Z with utcnow
        from datetime import timezone
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        summary_val = article.get('eng_summary', '')
        summary_section = f"## Executive Summary\n{summary_val}\n\n" if summary_val else ""
        formatted_eng_content = _format_readable_content(article.get('eng_content', 'Content not localized yet.'))
        content_body = f"{summary_section}## Strategic Deep-Dive\n{formatted_eng_content}"

    # [V3.1] Frontmatter Generation
    
    safe_title = title.replace('"', "'")
    safe_desc = desc_val.replace('"', "'")
    is_featured = "true" if article.get('featured') else "false"

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
    
    categories = ["ai-models", "ai-tools", "gpu-chips", "pc-robotics", "game-optimization", "ai-gameplay", "tutorials", "compare"]
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
