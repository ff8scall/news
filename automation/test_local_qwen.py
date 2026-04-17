import os
import sys
import logging
import time
import shutil
from ai_writer import AIWriter
from harvester_v3 import HarvesterV3
from ai_news_editor import NewsEditor
from news_main import create_hugo_post, sanitize_slug

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ProfilingLocalQwen")

def test_profiled_generation():
    writer = AIWriter()
    harvester = HarvesterV3(test_mode=True)
    editor = NewsEditor(writer=writer)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    logger.info("--- [START PROFILING] ---")
    
    # 1. 뉴스 수집 시간 측정
    t_start = time.time()
    news_items, _ = harvester.fetch_all(limit_per_cat=3) # 조금 더 많은 후보군 중 하나 선택
    t_harvest = time.time()
    logger.info(f"[TIMER] News Harvesting took {t_harvest - t_start:.2f}s")
    
    if not news_items:
        logger.warning("No fresh news. Using a fallback hot topic.")
        target_item = {
            'title': 'NVIDIA Blackwell GPU Architecture Deep Dive: Performance and Efficiency',
            'url': 'https://example.com/nvidia-blackwell',
            'description': 'Analyzing the new Blackwell architecture and its impact on AI training and inference.',
            'source_name': 'Tech Profile',
            'eng_category_slug': 'gpu-chips'
        }
    else:
        # 첫 번째 아이템 선택
        target_item = news_items[0]
        
    logger.info(f"Target Topic: {target_item['title']}")
    
    # 2. 분석 및 작성 단계별 측정 (review_batch 내부 로직 분해 시뮬레이션)
    model_name = "qwen2.5-coder:14b"
    
    try:
        # A. Scoring & English Analysis
        t0 = time.time()
        logger.info("[STEP 1] Starting English Event Analysis (Local Inference)...")
        event_report_en = editor._get_full_event_analysis([target_item], model=model_name)
        t1 = time.time()
        logger.info(f"[TIMER] Step 1 (EN Analysis) took {t1 - t0:.2f}s")
        
        if not event_report_en:
            logger.error("English analysis failed.")
            return

        # B. Localization (Korean Translation & Article Structure)
        t2 = time.time()
        logger.info("[STEP 2] Starting Korean Localization & SEO Optimization (Local Inference)...")
        # review_batch의 나머지 로직을 직접 수행하여 시간 측정
        localize_prompt = f"""
        [PERSONA]: Tech News Editor & Technical Analyst.
        [TASK]: Localize the English report into a professional Korean tech article.
        [QUALITY & TONE]: Professional, Analytical, No AI Filler.
        [OUTPUT STRUCTURE]: {editor.writer.generate_content("Give me the JSON schema for news", model="gemini-flash-latest") if False else "JSON"}
        [REPORT CONTEXT]: {event_report_en}
        """
        # 실제 review_batch 내부의 localize_prompt 로직 재현
        res = editor.writer.generate_content(event_report_en, role="writing", model=model_name) 
        # (간략화를 위해 직접 generate_content 호출. 실제로는 더 긴 프롬프트가 들어감)
        
        # 다시 제대로 된 프롬프트로 호출 (review_batch 내부 로직과 동일하게)
        from ai_news_editor import NEWS_JSON_SCHEMA
        full_localize_prompt = f"""
        [PERSONA]: Tech News Editor & Technical Analyst.
        [TASK]: Localize the English report into a professional Korean tech article.
        [OUTPUT STRUCTURE]: {NEWS_JSON_SCHEMA}
        [REPORT CONTEXT]: {event_report_en}
        """
        res = editor.writer.generate_content(full_localize_prompt, role="writing", model=model_name)
        draft = editor._extract_json_safe(res)
        t3 = time.time()
        logger.info(f"[TIMER] Step 2 (KR Localization) took {t3 - t2:.2f}s")
        
        if draft:
            # C. Post Processing & Image Gen (Saving)
            t4 = time.time()
            logger.info("[STEP 3] Starting Post-Processing & Image Generation...")
            article = draft
            article['sync_slug'] = sanitize_slug(target_item['title'])
            article['eng_content'] = event_report_en
            article['original_url'] = target_item.get('url', '')
            article['original_image_url'] = target_item.get('image')
            article['source_name'] = target_item.get('source_name', 'Tech Profile')
            
            original_cwd = os.getcwd()
            os.chdir(root_dir)
            try:
                create_hugo_post(article, lang='ko')
                create_hugo_post(article, lang='en')
            finally:
                os.chdir(original_cwd)
                
            t5 = time.time()
            logger.info(f"[TIMER] Step 3 (Post-Processing & Image) took {t5 - t4:.2f}s")
            
            total_time = t5 - t_start
            logger.info(f"--- [PROFILING COMPLETE] Total Time: {total_time:.2f}s ---")
            
            print(f"\nSummary:\n- Harvesting: {t_harvest - t_start:.1f}s\n- EN Analysis: {t1 - t0:.1f}s\n- KR Localization: {t3 - t2:.1f}s\n- Save & Image: {t5 - t4:.1f}s\n- Total: {total_time:.1f}s")
        else:
            logger.error("Localization failed to produce valid JSON.")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profiled_generation()
