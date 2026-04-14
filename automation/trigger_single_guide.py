import os
import sys
import logging
import json
import re
from datetime import datetime
import requests
import urllib.parse

# 상위 디렉토리 참조를 위해 path 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_guide_editor import GuideEditor
from ai_writer import AIWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SingleGuideTrigger")

def generate_and_save_thumbnail(image_prompt_core, slug_name):
    """[V8.1] 일자별 이미지 폴더 구조 및 화질 최적화"""
    aesthetic_base = ", minimalist dark mode tech aesthetic, isometric view, clean smooth surfaces, 8k resolution, highly detailed corporate editorial illustration --no text, no humans, no robots, no faces"
    
    final_prompt = (image_prompt_core if image_prompt_core else "Abstract tech geometry") + aesthetic_base
    print(f"[IMAGE] Creating thumbnail for {slug_name} with prompt: {final_prompt}")
    
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
            return f"/images/posts/{date_dir}/{slug_name}.jpg"
    except Exception as e:
        print(f"[IMAGE] Failed: {e}")
    return "/images/default-tech-bg.jpg"

def fix_frontmatter_image(md_content, img_path):
    """Frontmatter 내부에 image 경로를 정확히 삽입하거나 교체"""
    if 'image:' in md_content:
        return re.sub(r'image:\s*".*?"', f'image: "{img_path}"', md_content)
    else:
        # 첫 번째 --- 바로 다음에 삽입
        return md_content.replace('---\n', f'---\nimage: "{img_path}"\n', 1)

def main():
    editor = GuideEditor(model_name="gemma4:latest")
    
    topic = {
        'kor_title': 'FastAPI와 Gemini API를 활용한 실시간 뉴스 요약 서버 구축',
        'kor_content': 'Python FastAPI 프레임워크와 Google Gemini 1.5 Flash API를 결합하여, 실시간으로 뉴스를 분석하고 요약 결과를 반환하는 API 서버를 구축하는 상세 안내서입니다. 데이터 흐름 설계와 Pydantic을 이용한 구조화된 응답 처리를 포함합니다.'
    }
    
    # 1. 영문 및 한글 가이드 생성 (Strict No-Emoji)
    print("--- [1단계] 영문 가이드 생성 ---")
    en_md = editor.write_english_guide(topic)
    
    print("--- [2단계] 한글 가이드 번역 ---")
    ko_md = editor.translate_to_korean(en_md)
    
    slug = "fastapi-gemini-news-summarizer-v2"
    
    # 2. 이미지 생성
    img_prompt_match = re.search(r'image_prompt_core:\s*"(.*?)"', en_md)
    img_prompt = img_prompt_match.group(1) if img_prompt_match else "Abstract API data flow nodes"
    img_path = generate_and_save_thumbnail(img_prompt, slug)
    
    # 3. 이미지 필드 주입
    en_md = fix_frontmatter_image(en_md, img_path)
    ko_md = fix_frontmatter_image(ko_md, img_path)
    
    # 4. 양국 통합 파일 저장
    date_path = datetime.now().strftime("%Y/%m/%d")
    
    for lang in ['en', 'ko']:
        target_dir = f"content/{lang}/posts/{date_path}"
        os.makedirs(target_dir, exist_ok=True)
        filepath = f"{target_dir}/{slug}.md"
        
        content = en_md if lang == 'en' else ko_md
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(content)
        print(f"[{lang.upper()}] Saved: {filepath}")

    print(f"\n--- [성공] 양문 가이드 생성 완료 ---")
    print(f"이미지: {img_path}")

if __name__ == "__main__":
    main()
