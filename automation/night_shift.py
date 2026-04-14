import os
import sys
import time
import json
import logging
import re
from datetime import datetime
from ai_guide_editor import GuideEditor

# [로그 설정]
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LegoSia.NightShift")

class StateTracker:
    """[V9.0] Job State Management: Ensures resumable & atomic operations"""
    def __init__(self, state_file="automation/job_state.json"):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"guides": {}, "news": {}}
        return {"guides": {}, "news": {}}

    def save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)

    def is_done(self, section, slug, lang):
        return lang in self.state.get(section, {}).get(slug, [])

    def mark_done(self, section, slug, lang):
        if section not in self.state: self.state[section] = {}
        if slug not in self.state[section]: self.state[section][slug] = []
        if lang not in self.state[section][slug]:
            self.state[section][slug].append(lang)
            self.save_state()

def sanitize_filename(filename):
    clean = re.sub(r'[\\/*?:"<>|]', "", filename)
    return clean.replace(" ", "-")

GUIDE_TOPICS = [
    {"title": "Gemma 4 Local Server Setup Guide (Ollama/Windows)", "summary": "Full Implementation of Local LLM", "tech_data": "Ollama, Windows, NVIDIA GPU, REST API Integration"},
    {"title": "Stable Diffusion 3.5 Local Installation and LoRA Training", "summary": "Setup and personal character training", "tech_data": "SD 3.5 Large, ComfyUI/Forge, LoRA Fine-tuning workflow"},
    {"title": "Claude 3 API Integration with Local RAG Systems", "summary": "Building a private knowledge base with Anthropic", "tech_data": "Claude 3.5 Sonnet, LangChain, FAISS Vector DB, Python"},
    {"title": "VRAM Optimization for AI workloads on 8-12GB GPUs", "summary": "How to run large models on consumer hardware", "tech_data": "Quantization (GGUF/EXL2), Xformers, Flash Attention, Virtual Memory tricks"},
    {"title": "Fine-Tuning Llama 3 on Personal Data (Unsloth)", "summary": "Lightning fast fine-tuning guide", "tech_data": "Unsloth, QLoRA, HuggingFace Dataset, Python"},
    {"title": "Building a Local AI Coding Agent (Continue.dev/Aider)", "summary": "Automating your private dev workflow", "tech_data": "VS Code, Continue, DeepSeek Coder, Local LLM setup"},
    {"title": "Running Flux.1 (Black Forest Labs) on Windows", "summary": "High-fidelity local image generation", "tech_data": "Flux.1 [dev], GGUF version, Win-AMD/NVIDIA optimization"},
    {"title": "Real-time Voice AI with Whisper & Piper TTS", "summary": "Low-latency private voice interaction", "tech_data": "Whisper CTranslate2, Piper TTS, Python sounddevice"},
    {"title": "Setting up a Private PDF Analyzer (Nomic/PrivateGPT)", "summary": "Analysis of corporate documents without leaks", "tech_data": "Nomic Embed, LlamaCpp, Streamlit UI, local storage"}
]

def run_guide_engine():
    logger.info("[GUIDE] Resilient Engine V9.0 starting")
    editor = GuideEditor(model_name="gemma4:latest")
    tracker = StateTracker()
    
    for topic in GUIDE_TOPICS:
        try:
            safe_slug = sanitize_filename(topic['title'])
            
            # [V9.0] Skip if both EN and KO are already finished
            if tracker.is_done("guides", safe_slug, "en") and tracker.is_done("guides", safe_slug, "ko"):
                logger.info(f"[GUIDE] Skipping {safe_slug} - Already completed.")
                continue

            news_draft = {
                "kor_title": topic['title'],
                "kor_summary": topic['summary'],
                "kor_content": f"TECHNICAL CONSTRAINTS: {topic['tech_data']}", 
                "sync_slug": safe_slug
            }
            
            # Step 1: English (Only if not done)
            guide_en = None
            if not tracker.is_done("guides", safe_slug, "en"):
                logger.info(f"[GUIDE] Step 1: Writing English Original for {safe_slug}")
                guide_en = editor.write_english_guide(news_draft)
                if guide_en:
                    save_guide_file(guide_en, news_draft, lang='en')
                    tracker.mark_done("guides", safe_slug, "en")
            
            # Step 2: Korean (Only if not done)
            if not tracker.is_done("guides", safe_slug, "ko"):
                logger.info(f"[GUIDE] Step 2: Translating {safe_slug} to Korean")
                if not guide_en:
                    # In a real recovery, we might read the file from disk here
                    # To keep it simple, we re-gen EN if not in memory (fast in local anyway)
                    guide_en = editor.write_english_guide(news_draft)
                
                guide_ko = editor.translate_to_korean(guide_en)
                if guide_ko:
                    save_guide_file(guide_ko, news_draft, lang='ko')
                    tracker.mark_done("guides", safe_slug, "ko")
            
            git_commit_backup()
            time.sleep(20)
        except Exception as e:
            logger.error(f"[GUIDE] V9.0 Pipeline failed on {topic['title']}: {e}")

import urllib.parse
import requests

def generate_and_save_thumbnail(gemma_markdown, slug_name):
    """[V7.5] Controlled Freedom: AI Subject + Hardcoded Aesthetic Base"""
    match = re.search(r'image:\s*"([^"]+)"', gemma_markdown)
    core_subject = match.group(1) if match else "Abstract tech geometric neural networks"
    
    aesthetic_base = ", minimalist dark mode tech aesthetic, isometric view, clean smooth surfaces, 8k resolution, highly detailed corporate editorial illustration --no text, no humans, no robots, no faces"
    
    final_prompt = core_subject + aesthetic_base
    logger.info(f"[IMAGE] Creating thumbnail for {slug_name}: {core_subject[:50]}...")
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
    
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            date_dir = datetime.now().strftime("%Y/%m/%d")
            save_dir = f"static/images/posts/{date_dir}"
            os.makedirs(save_dir, exist_ok=True)
            
            save_path = f"{save_dir}/{slug_name}.jpg"
            with open(save_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"[IMAGE] Thumbnail saved: {save_path}")
            return f"/images/posts/{date_dir}/{slug_name}.jpg"
    except Exception as e:
        logger.error(f"[IMAGE] Generation failed: {e}")
    return "/images/default-tech-bg.jpg"

def save_guide_file(markdown_content, news_draft, lang='ko'):
    """[V8.0] 일자별 폴더 구조 적용 (YYYY/MM/DD)"""
    date_path = datetime.now().strftime("%Y/%m/%d")
    target_dir = f"content/{lang}/guides/{date_path}"
    os.makedirs(target_dir, exist_ok=True)
    
    safe_filename = sanitize_filename(news_draft['sync_slug'])
    filepath = os.path.join(target_dir, f"{safe_filename}.md")
    
    # [V7.6] Force Real-time Sync (HH:MM:SS)
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00') if lang == 'ko' else datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # [V7.5] Generate Thumbnail and link in Markdown
    img_path = generate_and_save_thumbnail(markdown_content, f"guide-{safe_filename}")
    
    # [V9.1] Replace AI Prompt with Real Image Path (Fix Duplicate Key)
    if img_path:
        markdown_content = re.sub(r'image_prompt_core:\s*".*"', f'image: "{img_path}"', markdown_content)
    
    # Force Timestamp Update in Frontmatter
    markdown_content = re.sub(r'date: ".*"', f'date: "{current_time}"', markdown_content)

    try:
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(markdown_content)
        return True
    except Exception as e:
        logger.error(f"[FILE] Error in {lang}: {e}")
        return False

def git_commit_backup():
    try:
        os.system("git add .")
        ctime = datetime.now().strftime("%Y-%m-%d %H:%M")
        os.system(f'git commit -m "Auto-backup: {ctime}"')
        logger.info("[GIT] Content backed up.")
    except:
        pass

if __name__ == "__main__":
    run_guide_engine()
