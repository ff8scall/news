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
from dataclasses import asdict

# 미래 날짜 문제를 방지하기 위해 10분(600초)의 마진을 두고 현재 시간보다 과거로 설정
POST_TIME_OFFSET = -600

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
    "ai": "인공지능·소프트웨어",
    "hardware": "컴퓨팅·하드웨어",
    "insights": "기술 분석·인사이트"
}

# [V1.1] Alignment with actual fallback filenames in static/images/fallbacks/
# [V4.0] 초정예 폴백 이미지 매핑
FALLBACK_MAP = {
    "ai": "ai-tech",
    "hardware": "hardware",
    "insights": "market-trend"
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
    POST_TIME_OFFSET += 5 
    
    # [V11.4] 프로젝트 루트 기준 절대 경로 산출 (어디서 실행해도 정해진 폴더에 저장)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    date_path = pub_date.strftime("%Y/%m/%d")
    target_dir = os.path.join(project_root, 'content', lang, 'posts', date_path)
    os.makedirs(target_dir, exist_ok=True)
    
    slug = article['sync_slug']
    cat_safe = sanitize_slug(article.get('category', 'ai-models'))
    
    # [V11.1] Unified Mirroring Template Logic
    prefix = 'kor' if lang == 'ko' else 'eng'
    
    title = article.get(f'{prefix}_title') or article.get('title')
    summary_list = article.get(f'{prefix}_summary') or article.get('summary', [])
    content = article.get(f'{prefix}_content') or article.get('content', '')
    insight = article.get(f'{prefix}_insight', '')
    description = article.get(f'{prefix}_description', '')
    keywords = article.get(f'{prefix}_keywords', [])
    
    # [V11.2] Smart Fallback: 필드 누락 시 상호 보완
    if not title:
        # 본문 첫 줄에서 제목 추출 시도
        if content:
            first_line = content.split('\n')[0].strip().strip('#').strip()
            title = first_line[:100] if len(first_line) > 5 else "Untitled Analysis"
        else:
            title = article.get('sync_slug', 'Untitled Article')

    if not summary_list or (isinstance(summary_list, list) and not summary_list):
        if description: 
            summary_list = [description]
        elif content:
            # 본문의 첫 번째 유효 문단을 요약으로 사용
            paragraphs = [p.strip() for p in content.split('\n') if p.strip() and not p.startswith('#')]
            summary_list = [paragraphs[0][:200] + "..."] if paragraphs else [title]
        else:
            summary_list = [title]

    if isinstance(summary_list, str): 
        summary_list = [summary_list]

    if not insight and content:
        # 본문 하단에 '시사점' 혹은 'Insight' 섹션이 있는지 확인하여 추출
        matches = re.findall(r'(?i)##\s*(?:시사점|인사이트|Insight|Conclusion)\s*\n(.*?)(?:\n##|$)', content, re.DOTALL)
        if matches:
            insight = matches[-1].strip()
            # 본문에서 해당 내용을 제거하여 중복 방지 (선택 사항, 여기선 일단 정보 보존 우선)

    # Titles & Labels
    summary_label = "핵심 요약" if lang == 'ko' else "Executive Summary"
    analysis_label = "상세 분석" if lang == 'ko' else "Strategic Deep-Dive"
    insight_label = "시사점" if lang == 'ko' else "Strategic Insights"
    
    # Date Formatting
    if lang == 'ko':
        date_str = pub_date.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    else:
        from datetime import timezone
        date_str = pub_date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Formatting Content
    summary_text = "\n".join([f"- {s}" for s in summary_list])
    formatted_content = _format_readable_content(content)
    formatted_insight = _format_readable_content(insight)
    
    # Image Tiered Strategy
    from image_manager import get_tiered_image
    thumbnail_url = article.get('thumbnail_image')
    if not thumbnail_url:
        thumbnail_url = get_tiered_image(article, slug)
        article['thumbnail_image'] = thumbnail_url 

    # Build Body
    content_body = f"## {summary_label}\n{summary_text}\n\n"
    if formatted_content:
        content_body += f"## {analysis_label}\n\n{formatted_content}\n\n"
    if formatted_insight:
        content_body += f"## {insight_label}\n\n{formatted_insight}"

    # Build Frontmatter
    # [V11.3] 줄바꿈 제거 및 따옴표 이스케이프 강화 (YAML 안정성)
    safe_title = title.replace('"', "'").replace("\n", " ").strip()
    safe_desc = (description if description else (summary_list[0] if summary_list else title)).replace('"', "'").replace("\n", " ").strip()
    is_featured = "true" if article.get('featured') else "false"
    tags_json = json.dumps(keywords, ensure_ascii=False)

    post_md = f"""---
title: "{safe_title}"
date: "{date_str}"
description: "{safe_desc}"
image: "{thumbnail_url}"
clusters: ["{article.get('cluster', 'ai')}"]
categories: ["{article.get('category', 'ai')}"]
tags: {tags_json}
featured: {is_featured}
---
{content_body}
"""
    filepath = os.path.join(target_dir, f"{slug}.md")
    with open(filepath, "w", encoding="utf-8-sig") as f: f.write(post_md)
    return True

def process_category(cat, items, editor, tracker, use_local=False, limit=1):
    """[Helper] Thread-safe category processing worker - returns number of processed items"""
    if not items: return 0
    
    model_name = "gemma4:26b" if use_local else None
    processed_count = 0
    
    for item in items:
        if processed_count >= limit: break
        
        # [V11.0] Premium Slug Strategy Integration
        cluster = item.get('cluster') or cat
        raw_slug = sanitize_slug(item['title'])
        if raw_slug and not raw_slug.isdigit():
            safe_slug = f"{cluster}-{raw_slug}"[:50].strip('-')
        else:
            article_id = hash_slug(item.get('url', ''))
            safe_slug = f"{cluster}-{cat}-{article_id}"
        
        # 이미 한 쪽이라도 되었거나 캐시가 있으면 진행 (둘 다 완료된 경우만 스킵)
        if tracker.is_done("news", safe_slug, "ko") and tracker.is_done("news", safe_slug, "en"): 
            continue

        try:
            start_time = time.time()
            logger.info(f"[PROCESS_START] [{cat}] Starting: {item['title'][:50]} (Slug: {safe_slug})")
            
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
    news_items_raw, stats = harvester.fetch_all(limit_per_cat=limit_per_cat + 2)
    logger.info(f"Harvested: {stats}")
    
    # [V11.1] Convert Dataclass to Dictionary for legacy compatibility
    news_items = [asdict(item) for item in news_items_raw]
    
    items_by_cat = {}
    for item in news_items:
        cat = item['eng_category_slug']
        if cat not in items_by_cat: items_by_cat[cat] = []
        items_by_cat[cat].append(item)
    
    categories = ["ai", "hardware", "insights"]
    total_published = 0
    published_urls = []
    
    # 정기 배치는 안정성을 위해 순차 처리 (Throttling 준수)
    for cat in categories:
        count = process_category(cat, items_by_cat.get(cat, []), editor, tracker, use_local, limit=limit_per_cat)
        total_published += count
    
    # [V11.5] URL 수집 로직 (발행 직후 최신 슬러그 기반으로 URL 생성)
    for cat in categories:
        items = items_by_cat.get(cat, [])
        for item in items:
            cluster = item.get('cluster') or cat
            raw_slug = sanitize_slug(item['title'])
            if raw_slug and not raw_slug.isdigit():
                safe_slug = f"{cluster}-{raw_slug}"[:50].strip('-')
            else:
                # hash_slug는 news_main.py에 정의되어 있음
                article_id = hashlib.md5(item.get('url', '').encode()).hexdigest()[:8]
                safe_slug = f"{cluster}-{cat}-{article_id}"
            
            # 오늘 날짜 기반 경로 생성 (create_hugo_post와 동일한 로직)
            date_path = datetime.now().strftime('%Y/%m/%d')
            
            # 이번 세션에 새로 완료된 것만 URL 리스트에 추가 (is_done 체크)
            if tracker.is_done("news", safe_slug, "ko"):
                published_urls.append(f"https://news.lego-sia.com/posts/{date_path}/{safe_slug}/")
            if tracker.is_done("news", safe_slug, "en"):
                published_urls.append(f"https://news.lego-sia.com/en/posts/{date_path}/{safe_slug}/")

    # IndexNow 알림 발송
    if published_urls:
        unique_urls = list(set(published_urls))
        notify_indexnow(unique_urls)

    summary_msg = f"✅ Production Pipeline Cycle Completed!\nSuccessfully Published: {total_published} articles.\nIndexed: {len(unique_urls) if published_urls else 0} URLs."
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
    
    try:
        if args.mode == "premium":
            logger.info("[MODE: PREMIUM] Redirecting to NotebookLM Synthesis Pipeline...")
            send_telegram_report("🚀 [PREMIUM] 뉴스 파이프라인 합성이 시작되었습니다.")
            from notebooklm_prep import process_macro_synthesis
            process_macro_synthesis(limit_per_cat=args.limit)
            report = "✅ Premium Pipeline Phase 1 Completed Successfully."
        else:
            logger.info("[MODE: LEGACY] Starting standard daily pipeline...")
            send_telegram_report("🚀 [LEGACY] 표준 뉴스 파이프라인이 시작되었습니다.")
            report = manage_news_pipeline(limit_per_cat=args.limit, use_local=args.local)
    except Exception as e:
        report = f"❌ 파이프라인 중단 에러 발생: {str(e)}"
        logger.error(report)
        
    try:
        send_telegram_report(report)
    except Exception as e:
        logger.error(f"Telegram Fail: {e}")
    print(f"Pipeline finished.")

if __name__ == "__main__": 
    main()
