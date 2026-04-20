import os
import requests
import urllib.parse
import time
import logging
import re
from datetime import datetime

logger = logging.getLogger("ImageManager")

# [V3.0] 프로젝트 루트 기준 경로 자동 탐색
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

DEFAULT_LIB_ROOT = os.path.join(STATIC_ROOT, "images/defaults")
POST_IMAGE_ROOT = os.path.join(STATIC_ROOT, "images/posts")
FALLBACK_WEB_PATH = "/images/fallbacks"

# 클러스터 정규화 및 폴백 매핑
CLUSTER_MAP = {
    "ai": "ai-tech",
    "hardware": "hardware",
    "insights": "market-trend",
    "news": "tech-biz",
    "tech": "ai-tech",
    "guides": "ai-tools",
    "ai-models-tools": "ai-models",
    "gpu-hardware": "semi-hbm",
    "ai-gaming": "game-tech",
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, timeout=(5, 15), headers=headers)
        if resp.status_code == 200:
            content = resp.content
            if len(content) > 1000: # 최소 1KB 이상이어야 정상 이미지로 간주
                with open(save_path, 'wb') as f: f.write(content)
                logger.info(f" [Tier 1] [OK] Original Image Downloaded: {web_path}")
                return web_path
            else:
                logger.warning(f" [Tier 1] [FAIL] Image content too small from: {url}")
        else:
            logger.warning(f" [Tier 1] [FAIL] HTTP {resp.status_code} for: {url}")
    except Exception as e:
        logger.warning(f" [Tier 1] [ERROR] Download Failed {url}: {e}")
    
    return None

def find_matching_default(cluster, keywords):
    """[Tier 2] 키워드 라이브러리에서 매칭되는 이미지 검색"""
    # CLUSTER_MAP에서 디렉토리명 추출 (기본값 tech)
    target_cluster = CLUSTER_MAP.get(cluster.lower(), "ai-tech").split('-')[0]
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
        logger.info(f" [Tier 3] [START] Requesting AI Generation for: {slug}")
        resp = requests.get(api_url, timeout=45)
        if resp.status_code == 200:
            content = resp.content
            # 최소 10KB 이상이어야 유효한 AI 생성 이미지로 간주 (너무 작으면 엑박일 확률 높음)
            if len(content) > 10240: 
                # (A) 포스트용 저장
                date_dir = datetime.now().strftime("%Y/%m/%d")
                post_dir = os.path.join(POST_IMAGE_ROOT, date_dir)
                os.makedirs(post_dir, exist_ok=True)
                post_save_path = os.path.join(post_dir, f"{slug}_gen.jpg")
                with open(post_save_path, 'wb') as f: f.write(content)
                
                # (B) 라이브러리용 저장 (첫 번째 유효 키워드 기준)
                target_cluster = CLUSTER_MAP.get(cluster.lower(), "ai-tech").split('-')[0]
                if keywords:
                    for kw in keywords:
                        safe_kw = sanitize_name(kw)
                        if not safe_kw or len(safe_kw) < 2: continue
                        
                        lib_dir = os.path.join(DEFAULT_LIB_ROOT, target_cluster)
                        os.makedirs(lib_dir, exist_ok=True)
                        lib_save_path = os.path.join(lib_dir, f"{safe_kw}.jpg")
                        
                        if not os.path.exists(lib_save_path):
                            with open(lib_save_path, 'wb') as f: f.write(content)
                            logger.info(f" [Tier 3] [CACHE] New Keyword Image Saved: {target_cluster}/{safe_kw}.jpg")
                            break 
                
                logger.info(f" [Tier 3] [OK] AI Generation Successful: {slug}_gen.jpg")
                return f"/images/posts/{date_dir}/{slug}_gen.jpg"
            else:
                logger.warning(f" [Tier 3] [FAIL] API returned invalid/tiny image: {len(content)} bytes")
        else:
            logger.warning(f" [Tier 3] [FAIL] API HTTP Status: {resp.status_code}")
    except Exception as e:
        logger.error(f" [Tier 3] [ERROR] AI Generation Failed: {e}")
    
    return None

def get_tiered_image(article, slug):
    """메인 진입점: 계층적 이미지 선택 로직"""
    # 0. 건너뛰기 설정 확인 (원본 및 생성만 스킵)
    skip_ai = (os.environ.get("SKIP_AI_IMAGE") == "1")

    # 1. Tier 1: 원본 이미지
    orig_url = article.get('original_image_url') or article.get('original_image')
    if orig_url:
        res = download_image(orig_url, slug)
        if res: return res

    # 2. Tier 2: 라이브러리 매칭
    cluster = article.get('cluster', 'tech')
    # 키워드 목록 합치기
    keywords = article.get('eng_keywords', []) + article.get('kor_keywords', [])
    
    lib_res = find_matching_default(cluster, keywords)
    if lib_res: return lib_res

    # 3. Tier 3: API 생성
    if not skip_ai:
        prompt = article.get('image_prompt_core') or article.get('eng_title')
        gen_res = generate_and_cache(prompt, cluster, keywords, slug)
        if gen_res: return gen_res

    # 4. Fallback (전혀 없을 경우) - 명시적으로 존재하는 파일명으로 보장
    fallback_file = CLUSTER_MAP.get(cluster.lower(), "ai-tech")
    
    # 파일이 존재하는지 최종 확인 후 없으면 가장 기본인 ai-tech로
    final_path = f"{FALLBACK_WEB_PATH}/{fallback_file}.jpg"
    return final_path
