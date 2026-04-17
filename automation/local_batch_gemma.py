import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from harvester_v3 import HarvesterV3
from ai_news_editor import NewsEditor
from ai_writer import AIWriter
from news_main import StateTracker, sanitize_slug, create_hugo_post
from common_utils import send_telegram_report

# [V1.1] Local Ultra-Fast Qwen2.5-Coder Synchronizer
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LegoSia.LocalQwen")

def process_category_local(cat, items, editor, tracker):
    """[Local Only] Forced Parallel Gemma4 Worker"""
    if not items: return None
    
    # 로컬은 스로틀링 없이 qwen2.5-coder:14b만 타겟팅
    model_name = "qwen2.5-coder:14b"
    
    for item in items:
        safe_slug = sanitize_slug(item['title'])
        if tracker.is_done("news", safe_slug, "ko"): continue

        try:
            logger.info(f"🚀 [LOCAL_START] [{cat}] Inference: {item['title'][:50]}")
            
            t0 = time.time()
            # NewsEditor.review_batch에서 내부적으로 AIWriter.generate_content(model='qwen2.5-coder:14b') 호출
            article_data_list = editor.review_batch([item], model=model_name)
            
            if article_data_list:
                article_data = article_data_list[0]
                article_data['sync_slug'] = safe_slug
                
                # Hugo 포스트 생성 (영문/한글)
                create_hugo_post(article_data, lang='en')
                tracker.mark_done("news", safe_slug, "en")
                create_hugo_post(article_data, lang='ko')
                tracker.mark_done("news", safe_slug, "ko")
                
                duration = time.time() - t0
                msg = f"✅ [LOCAL_SUCCESS] [{cat}] Finished in {duration:.1f}s: {article_data.get('kor_title')}"
                logger.info(msg)
                return msg
        except Exception as e:
            logger.error(f"❌ [LOCAL_FAIL] {cat}: {e}")
    return None

def main():
    logger.info("--- ⚡ Starting Local Ultra-Stable Qwen2.5-Coder Sync (2 Workers) ---")
    logger.info("--- [NOTE] Parallelism set to 2 to ensure smooth multitasking. ---")
    
    harvester = HarvesterV3()
    tracker = StateTracker()
    writer = AIWriter()
    editor = NewsEditor(writer=writer)
    
    # 1. 수집
    news_items, stats = harvester.fetch_all(limit_per_cat=3)
    logger.info(f"Harvested Stats: {stats}")
    
    items_by_cat = {}
    for item in news_items:
        cat = item['eng_category_slug']
        if cat not in items_by_cat: items_by_cat[cat] = []
        items_by_cat[cat].append(item)
    
    categories = ["ai-models", "ai-tools", "gpu-chips", "pc-robotics", "game-optimization", "ai-gameplay", "tutorials", "compare"]
    published_results = []
    
    # 2. 2중 병렬 가동 (안정 모드)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_category_local, cat, items_by_cat.get(cat, []), editor, tracker): cat for cat in categories}
        import concurrent.futures
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: published_results.append(res)

    report = f"⚡ [Qwen2.5-Coder Local Sync Complete]\nSuccessfully Synchronized: {len(published_results)}/8\n\n" + "\n".join(published_results)
    logger.info(report)
    
    # 텔레그램 발송
    try:
        send_telegram_report(report)
    except:
        pass

if __name__ == "__main__":
    main()
