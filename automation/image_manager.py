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

# [V5.0] 신규 4대 대메뉴 체제 이미지 매핑 (static/images/defaults 하위 폴더와 매칭)
CLUSTER_MAP = {
    "ai": "ai-tech",
    "hardware": "hardware-infra",
    "insights": "insights-analysis",
    "markets": "markets-biz"
}

# [V6.0] AI 이미지 스타일 셔플링을 위한 리스트
AESTHETIC_STYLES = [
    ", high-tech minimalism, cinematic 3D render, dark metallic texture, neon accents, isometric perspective, Unreal Engine 5 aesthetic, 8k resolution",
    ", blueprint technical drawing style, professional engineering scheme, clean white background, blueprint blue lines, highly detailed, architectural",
    ", futuristic organic architecture, biomimetic design, soft ambient lighting, high-end product photography, elegant curves, glass and silver textures",
    ", cyberpunk street aesthetic, intense moody lighting, terminal interface overlays, glitch art subtle accents, vaporware color palette",
    ", corporate flat design illustration, modern tech startup style, vibrant vector graphics, clean professional iconography"
]

def sanitize_name(name):
    """파일명으로 안전한 이름 생성"""
    if not name: return "default"
    clean = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
    return clean.strip('_')

def download_image(url, slug):
    """[Tier 1] 원본 이미지 다운로드 - [V6.2] 헤더 보강 및 유효성 검사 강화"""
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
        # [V6.2] 정교한 헤더 설정 (Referer, Accept 등 추가)
        domain = urllib.parse.urlparse(url).netloc
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': f"https://{domain}/",
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        resp = requests.get(url, timeout=(10, 30), headers=headers, stream=True)
        
        if resp.status_code == 200:
            # Content-Type 확인 (이미지인지)
            ct = resp.headers.get('Content-Type', '').lower()
            if 'image' not in ct and not any(ext in ct for ext in ['jpg', 'jpeg', 'png', 'webp']):
                logger.warning(f" [Tier 1] [SKIP] Not an image (Content-Type: {ct}): {url}")
                return None
                
            content = resp.content
            if len(content) > 2048: # 최소 2KB 이상 (너무 작은 파일은 깨진 것으로 간주)
                with open(save_path, 'wb') as f: f.write(content)
                logger.info(f" [Tier 1] [OK] Original Image Saved: {web_path}")
                return web_path
            else:
                logger.warning(f" [Tier 1] [FAIL] Image too small ({len(content)} bytes) from: {url}")
        else:
            logger.warning(f" [Tier 1] [FAIL] HTTP {resp.status_code} for: {url}")
    except Exception as e:
        logger.warning(f" [Tier 1] [ERROR] Download Failed {url}: {e}")
    
    return None

def find_matching_default(cluster, keywords):
    """[Tier 2] 키워드 라이브러리에서 매칭되는 이미지 검색 (랜덤 버전 지원)"""
    import random
    target_cluster = CLUSTER_MAP.get(cluster.lower(), "ai-tech").split('-')[0]
    cluster_dir = os.path.join(DEFAULT_LIB_ROOT, target_cluster)
    
    if not os.path.exists(cluster_dir):
        os.makedirs(cluster_dir, exist_ok=True)
        return None

    # 키워드 우선순위: 앞쪽 키워드부터 매칭 시도
    for kw in keywords:
        safe_kw = sanitize_name(kw)
        if not safe_kw or len(safe_kw) < 2: continue
        
        # [V6.0] 다중 버전 탐색 (예: ai.jpg, ai_1.jpg, ai_2.jpg ...)
        candidates = []
        for ext in ['.jpg', '.png', '.webp']:
            # 기본 파일
            base_path = os.path.join(cluster_dir, f"{safe_kw}{ext}")
            if os.path.exists(base_path):
                candidates.append(f"/images/defaults/{target_cluster}/{safe_kw}{ext}")
            
            # 숫자 접미사가 붙은 버전들 (1~5)
            for i in range(1, 6):
                version_path = os.path.join(cluster_dir, f"{safe_kw}_{i}{ext}")
                if os.path.exists(version_path):
                    candidates.append(f"/images/defaults/{target_cluster}/{safe_kw}_{i}{ext}")
        
        if candidates:
            selected = random.choice(candidates)
            logger.info(f" [Tier 2] Library Match: {selected} (Keyword: {kw}, Pool Size: {len(candidates)})")
            return selected
    
    return None

def generate_and_cache(prompt, cluster, keywords, slug):
    """[Tier 3] API 생성 및 라이브러리 자동 저장 (5초 지연 및 백오프 적용)"""
    import random
    import time
    
    # [V6.1] 사용자 가이드: 호출 간격 기본 5초 보장
    time.sleep(5)
    
    # 스타일 셔플링
    style = random.choice(AESTHETIC_STYLES)
    
    # [V6.2] 프롬프트 보강: 제목이나 프롬프트에서 핵심 키워드 추출 시도
    clean_prompt = prompt if prompt else "Abstract futuristic technology"
    # 너무 짧은 경우 키워드들 결합
    if len(clean_prompt.split()) < 5 and keywords:
        clean_prompt += f", {', '.join(keywords[:2])}"
    
    final_prompt = clean_prompt + style + " --no text, no faces, no humans"
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
    
    # [V6.1] 지수 백오프 적용 (최대 2회 시도 - 지연 방지)
    wait_time = 3
    for attempt in range(2):
        try:
            logger.info(f" [Tier 3] [START] Requesting AI (Attempt {attempt+1}): {slug}")
            resp = requests.get(api_url, timeout=15)
            
            if resp.status_code == 200:
                content = resp.content
                if len(content) > 10240: 
                    # 포스트용 저장
                    date_dir = datetime.now().strftime("%Y/%m/%d")
                    post_dir = os.path.join(POST_IMAGE_ROOT, date_dir)
                    os.makedirs(post_dir, exist_ok=True)
                    post_save_path = os.path.join(post_dir, f"{slug}_gen.jpg")
                    with open(post_save_path, 'wb') as f: f.write(content)
                    
                    # 라이브러리용 저장
                    target_cluster = CLUSTER_MAP.get(cluster.lower(), "ai-tech").split('-')[0]
                    if keywords:
                        for kw in keywords:
                            safe_kw = sanitize_name(kw)
                            if not safe_kw or len(safe_kw) < 2: continue
                            lib_dir = os.path.join(DEFAULT_LIB_ROOT, target_cluster)
                            os.makedirs(lib_dir, exist_ok=True)
                            slot = random.randint(1, 5)
                            lib_save_path = os.path.join(lib_dir, f"{safe_kw}_{slot}.jpg")
                            with open(lib_save_path, 'wb') as f: f.write(content)
                            break 
                    
                    return f"/images/posts/{date_dir}/{slug}_gen.jpg"
            
            elif resp.status_code == 429:
                wait_time *= 2
                logger.warning(f" [Tier 3] [429 ERROR] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.warning(f" [Tier 3] [FAIL] HTTP {resp.status_code} for AI Image")
                break
                
        except Exception as e:
            logger.warning(f" [Tier 3] [TIMEOUT/ERROR] Attempt {attempt+1} failed: {e}")
            if attempt < 1: time.sleep(2)
            
    return None

def get_tiered_image(article, slug):
    """메인 진입점: 계층적 이미지 선택 로직 (v6.1 랜덤 폴백 강화)"""
    import random
    import hashlib
    
    # 0. 건너뛰기 설정 확인
    skip_ai = (os.environ.get("SKIP_AI_IMAGE") == "1")

    # 1. Tier 1: 원본 이미지 (최우선)
    orig_url = article.get('original_image_url') or article.get('original_image')
    if orig_url:
        res = download_image(orig_url, slug)
        if res: return res

    # 2. Tier 2: 라이브러리 매칭 (30% 확률로 건너뛰어 신규 생성 유도)
    cluster = article.get('cluster', 'tech')
    keywords = article.get('eng_keywords', []) + article.get('kor_keywords', [])
    
    lib_res = find_matching_default(cluster, keywords)
    if lib_res and random.random() > 0.3: 
        return lib_res

    # 3. Tier 3: AI 신규 생성 (5초 지연 적용됨)
    if not skip_ai:
        prompt = article.get('image_prompt_core') or article.get('eng_title')
        gen_res = generate_and_cache(prompt, cluster, keywords, slug)
        if gen_res: return gen_res
    
    # 4. 재사용 폴백 (생성 실패 시 라이브러리 이미지라도 사용)
    if lib_res: return lib_res

    # 5. [V6.1] 최종 랜덤 폴백 (폴더 내 19종 중 랜덤 선택)
    # 슬러그를 시드로 사용하여 동일 기사는 동일 이미지를 유지하도록(Consistency) 구현
    try:
        # static/images/fallbacks/ 폴더 내 파일 목록 가져오기
        fb_dir = os.path.join(STATIC_ROOT, "images/fallbacks")
        if os.path.exists(fb_dir):
            files = [f for f in os.listdir(fb_dir) if f.endswith('.jpg')]
            if files:
                # 슬러그의 해시값을 인덱스로 사용하여 결정적 랜덤(Deterministic Random) 구현
                idx = int(hashlib.md5(slug.encode()).hexdigest(), 16) % len(files)
                selected = files[idx]
                logger.info(f" [Tier 5] Random Fallback Selected: {selected} (Slug: {slug})")
                return f"/images/fallbacks/{selected}"
    except Exception as e:
        logger.error(f" [Tier 5] Error choosing random fallback: {e}")

    # 최후의 수단 (매핑된 기본 파일)
    fallback_file = CLUSTER_MAP.get(cluster.lower(), "ai-tech")
    return f"/images/fallbacks/{fallback_file}.jpg"
