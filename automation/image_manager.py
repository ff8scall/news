import os
import requests
import urllib.parse
import time
import logging
import re
from datetime import datetime

logger = logging.getLogger("ImageManager")

# 기본 경로 설정
DEFAULT_LIB_ROOT = "static/images/defaults"
POST_IMAGE_ROOT = "static/images/posts"
FALLBACK_WEB_PATH = "/images/fallbacks"

# 클러스터 정규화 매핑
CLUSTER_MAP = {
    "ai": "ai",
    "hardware": "hardware",
    "insights": "insights",
    "news": "news",
    "tech": "tech"
}

def sanitize_name(name):
    """파일명으로 안전한 이름 생성"""
    if not name: return "default"
    clean = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
    return clean.strip('_')

def download_image(url, slug):
    """[Tier 1] 원본 이미지 다운로드"""
    if not url or not str(url).startswith('http'):
        return None
    
    # 확장자 체크
    lower_url = url.lower().split('?')[0]
    valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    if not any(ext in lower_url for ext in valid_exts) or 'html' in lower_url:
        return None

    date_dir = datetime.now().strftime('%Y/%m/%d')
    save_dir = os.path.join(POST_IMAGE_ROOT, date_dir)
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"{slug}.jpg"
    save_path = os.path.join(save_dir, filename)
    web_path = f"/images/posts/{date_dir}/{filename}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, timeout=(5, 15), headers=headers)
        if resp.status_code == 200:
            with open(save_path, 'wb') as f: f.write(resp.content)
            logger.info(f" [Tier 1] Downloaded: {web_path}")
            return web_path
    except Exception as e:
        logger.warning(f" [Tier 1] Failed: {e}")
    
    return None

def find_matching_default(cluster, keywords):
    """[Tier 2] 키워드 라이브러리에서 매칭되는 이미지 검색"""
    target_cluster = CLUSTER_MAP.get(cluster.lower(), "tech")
    cluster_dir = os.path.join(DEFAULT_LIB_ROOT, target_cluster)
    
    if not os.path.exists(cluster_dir):
        os.makedirs(cluster_dir, exist_ok=True)
        return None

    # 키워드 우선순위: 앞쪽 키워드부터 매칭 시도
    for kw in keywords:
        safe_kw = sanitize_name(kw)
        if not safe_kw or len(safe_kw) < 2: continue
        
        # .jpg, .png, .webp 순서로 검색
        for ext in ['.jpg', '.png', '.webp']:
            potential_path = os.path.join(cluster_dir, f"{safe_kw}{ext}")
            if os.path.exists(potential_path):
                web_path = f"/images/defaults/{target_cluster}/{safe_kw}{ext}"
                logger.info(f" [Tier 2] Library Match: {web_path} (Keyword: {kw})")
                return web_path
    
    return None

def generate_and_cache(prompt, cluster, keywords, slug):
    """[Tier 3] API 생성 및 라이브러리 자동 저장"""
    # 1. 이미지 생성
    aesthetic_base = ", high-tech minimalism, cinematic 3D render, dark metallic texture, neon accents, isometric perspective, Unreal Engine 5 aesthetic, 8k resolution --no text, no faces, no humans"
    final_prompt = (prompt if prompt else "Abstract futuristic technology") + aesthetic_base
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
    
    try:
        logger.info(f" [Tier 3] Calling API for: {slug}")
        resp = requests.get(api_url, timeout=45)
        if resp.status_code == 200 and len(resp.content) > 5000:
            content = resp.content
            
            # (A) 포스트용 저장
            date_dir = datetime.now().strftime("%Y/%m/%d")
            post_dir = os.path.join(POST_IMAGE_ROOT, date_dir)
            os.makedirs(post_dir, exist_ok=True)
            post_save_path = os.path.join(post_dir, f"{slug}_gen.jpg")
            with open(post_save_path, 'wb') as f: f.write(content)
            
            # (B) 라이브러리용 저장 (첫 번째 유효 키워드 기준)
            target_cluster = CLUSTER_MAP.get(cluster.lower(), "tech")
            if keywords:
                for kw in keywords:
                    safe_kw = sanitize_name(kw)
                    if not safe_kw or len(safe_kw) < 2: continue
                    
                    lib_dir = os.path.join(DEFAULT_LIB_ROOT, target_cluster)
                    os.makedirs(lib_dir, exist_ok=True)
                    lib_save_path = os.path.join(lib_dir, f"{safe_kw}.jpg")
                    
                    if not os.path.exists(lib_save_path):
                        with open(lib_save_path, 'wb') as f: f.write(content)
                        logger.info(f" [CACHE] Saved to library: {target_cluster}/{safe_kw}.jpg")
                        break # 하나만 저장
            
            return f"/images/posts/{date_dir}/{slug}_gen.jpg"
    except Exception as e:
        logger.error(f" [Tier 3] API Fail: {e}")
    
    return None

def get_tiered_image(article, slug):
    """메인 진입점: 계층적 이미지 선택 로직"""
    # 0. 건너뛰기 설정 확인
    if os.environ.get("SKIP_AI_IMAGE") == "1":
        return None

    # 1. Tier 1: 원본 이미지
    orig_url = article.get('original_image_url') or article.get('original_image')
    if orig_url:
        res = download_image(orig_url, slug)
        if res: return res

    # 2. Tier 2: 라이브러리 매칭
    cluster = article.get('cluster', 'tech')
    # 키워드 목록 합치기 (영문 우선 혹은 국문 우선 선택 가능)
    keywords = article.get('eng_keywords', []) + article.get('kor_keywords', [])
    
    lib_res = find_matching_default(cluster, keywords)
    if lib_res: return lib_res

    # 3. Tier 3: API 생성
    prompt = article.get('image_prompt_core') or article.get('eng_title')
    gen_res = generate_and_cache(prompt, cluster, keywords, slug)
    if gen_res: return gen_res

    # 4. Fallback (전혀 없을 경우)
    fallback_key = CLUSTER_MAP.get(cluster.lower(), "tech")
    # 기존 fallback 폴더의 파일명과 맞춤 (ai-tech.jpg 등)
    if fallback_key == "ai": fallback_key = "ai-tech"
    elif fallback_key == "tech": fallback_key = "ai-tech"
    
    return f"{FALLBACK_WEB_PATH}/{fallback_key}.jpg"
