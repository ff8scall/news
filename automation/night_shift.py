import json
import os
import re
import time
import logging
import subprocess
from ai_guide_editor import GuideEditor
from ai_news_editor import NewsEditor
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LegoSia.NightShift")

GUIDE_TOPICS = [
    {
        "title": "Gemma 4 Local Server Setup Guide (Ollama/Windows)", 
        "summary": "Building a private LLM server using Ollama with Gemma 4 on Windows 11.",
        "tech_data": "Backend: Ollama v0.1.28+, CUDA 12.1. Framework: FastAPI for API wrapper. Requirements: RTX 3060+ (12GB)."
    },
    {
        "title": "Stable Diffusion 3.5 Local Installation and LoRA Training", 
        "summary": "Step-by-step technical guide for SD 3.5 inference and fine-tuning on consumer GPUs.",
        "tech_data": "Backend: ComfyUI or SD-forge. Training: Kohya_ss. Requirements: 12GB VRAM (Inference w/ quantized fp8), 24GB VRAM (Training)."
    },
    {
        "title": "Claude 3 API Integration with Local RAG Systems", 
        "summary": "Architecting a hybrid AI system using Anthropics Claude 3 and local vector databases.",
        "tech_data": "Framework: LangChain. Backend: ChromaDB (Local). API: Claude 3 Sonnet/Opus for reasoning."
    },
    {
        "title": "VRAM Optimization for AI workloads on 8-12GB GPUs", 
        "summary": "Deep-dive into memory management for running heavy models on limited hardware.",
        "tech_data": "Techniques: xformers, 8-bit Adam optimizer, Gradient Checkpointing, CPU Offloading, Quantization (bnb)."
    }
]

def sanitize_filename(text):
    """[V6.0] Windows compatible filename sanitizer"""
    if not text: return "topic"
    clean = re.sub(r'[^a-zA-Z0-9가-힣\s-]', '', text).strip()
    return re.sub(r'\s+', '-', clean)[:50]

def git_commit_backup():
    """[V6.0] Automated Git commit for data safety"""
    try:
        subprocess.run(["git", "add", "content/"], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-backup: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=False)
        logger.info("[GIT] Content backed up.")
    except Exception as e:
        logger.warning(f"[GIT] Error: {e}")

def run_news_engine(limit=10):
    """[V6.0] News harvesting with bilingual support"""
    logger.info(f"[NEWS] Engine starting with limit {limit}")
    try:
        subprocess.run(["python", "automation/news_main.py", "--limit", str(limit)], check=True)
        git_commit_backup()
    except Exception as e:
        logger.error(f"[NEWS] Error: {e}")

def run_guide_engine():
    """[V6.0] Technical Guide generation with Deep Search context"""
    logger.info("[GUIDE] Technical documentation loop starting")
    editor = GuideEditor(model_name="gemma4:latest")
    
    for topic in GUIDE_TOPICS:
        try:
            safe_slug = sanitize_filename(topic['title'])
            logger.info(f"[GUIDE] Writing: {topic['title']}")
            
            # [V6.0] Technical Injection: Provide real frameworks and constraints
            rich_context = f"""
            TECHNICAL CONSTRAINTS FOR {topic['title']}:
            - {topic['tech_data']}
            - Objective: Produce a professional CLI-based manual following Phase 1-4.
            - Format: No flowery intro. Start with Overview then Phase 1.
            """
            
            news_draft = {
                "kor_title": topic['title'],
                "kor_summary": topic['summary'],
                "kor_content": rich_context, 
                "sync_slug": safe_slug
            }
            
            # KO/EN generation
            for lang in ['ko', 'en']:
                guide = editor.write_guide(news_draft, lang=lang)
                if guide:
                    create_guide_post_manual(guide, news_draft, lang=lang)
            
            git_commit_backup()
            time.sleep(15)
        except Exception as e:
            logger.error(f"[GUIDE] Critical failure on {topic['title']}: {e}")

def create_guide_post_manual(guide_data, news_draft, lang='ko'):
    date_path = datetime.now().strftime("%Y/%m")
    target_dir = f"content/{lang}/guides/{date_path}"
    os.makedirs(target_dir, exist_ok=True)
    
    safe_filename = sanitize_filename(news_draft['sync_slug'])
    filepath = os.path.join(target_dir, f"{datetime.now().strftime('%d')}-{safe_filename}.md")
    
    date_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00') if lang == 'ko' else datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    safe_title = guide_data.get('guide_title', 'No Title').replace('"', "'")
    safe_summary = guide_data.get('guide_summary', '').replace('"', "'")
    
    try:
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write("---\n")
            f.write(f'title: "{safe_title}"\n')
            f.write(f"date: {date_str}\n")
            f.write(f'summary: "{safe_summary}"\n')
            f.write(f"clusters: [\"guides\"]\n")
            f.write(f"categories: [\"tutorials\"]\n")
            f.write(f"difficulty: \"{guide_data.get('difficulty', 'Advanced')}\"\n")
            f.write(f"tags: {json.dumps(guide_data.get('tags', []), ensure_ascii=False)}\n")
            f.write("---\n\n")
            f.write(guide_data.get('guide_content', ''))
        return True
    except Exception as e:
        logger.error(f"[FILE] Error in {lang}: {e}")
        return False

if __name__ == "__main__":
    logger.info("[NIGHT-SHIFT] Starting Master Loop V6.0")
    run_guide_engine()
    run_news_engine(limit=10)
    logger.info("[NIGHT-SHIFT] Completed")
