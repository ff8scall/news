# -*- coding: utf-8 -*-
"""
[nlm_parser.py] NotebookLM 출력물 구조화 파서
==============================================
NotebookLM이 ---ARTICLE_START--- / ---ARTICLE_END--- 구분자로 출력한
구조화 데이터를 Python dict 리스트로 변환합니다.

모드 A (메가트렌드 에디토리얼): 마크다운 사설 → 단일 기사 dict
모드 B (개별 기사 고품질):      구분자 기반 → 다수 기사 dict 리스트
"""

import re
import json
import logging

logger = logging.getLogger("LegoSia.NLMParser")

# 모드 B 출력에서 파싱할 필드 매핑
FIELD_MAP = {
    "ID": "id",
    "ENG_TITLE": "eng_title",
    "KOR_TITLE": "kor_title",
    "TITLE": "eng_title",
    "CLUSTER": "cluster",
    "CATEGORY": "category",
    "ENG_SUMMARY": "eng_summary",
    "KOR_SUMMARY": "kor_summary",
    "SUMMARY": "eng_summary",
    "ENG_CONTENT": "eng_content",
    "KOR_CONTENT": "kor_content",
    "CONTENT": "eng_content",
    "KOR_INSIGHT": "kor_insight",
    "KEYWORDS_EN": "eng_keywords",
    "KEYWORDS_KR": "kor_keywords",
    "KEYWORDS": "eng_keywords",
    "IMAGE_PROMPT": "image_prompt_core",
}

# 유효한 클러스터 목록
VALID_CLUSTERS = [
    "ai-models-tools", "gpu-hardware", "ai-gaming", "guides", "megatrend"
]

# 유효한 카테고리 목록
VALID_CATEGORIES = [
    "ai-models", "ai-tools", "gpu-chips", "pc-robotics",
    "game-optimization", "ai-gameplay", "tutorials", "compare"
]

CLUSTER_MAP = {
    "ai-models": "ai-models-tools", "ai-tools": "ai-models-tools",
    "gpu-chips": "gpu-hardware", "pc-robotics": "gpu-hardware",
    "game-optimization": "ai-gaming", "ai-gameplay": "ai-gaming",
    "tutorials": "guides", "compare": "guides"
}


def parse_structured_articles(raw_text):
    """
    모드 B 전용: ---ARTICLE_START--- / ---ARTICLE_END--- 구분자 기반 파싱.
    
    Returns:
        list[dict]: Hugo create_hugo_post()에 바로 투입 가능한 기사 데이터 리스트
    """
    if not raw_text:
        logger.error("Empty text received for parsing.")
        return []

    # 구분자로 기사 블록 추출
    pattern = r'---ARTICLE_START---(.*?)---ARTICLE_END---'
    blocks = re.findall(pattern, raw_text, re.DOTALL)

    if not blocks:
        logger.warning("No ARTICLE_START/END blocks found. Attempting fallback parsing...")
        return _fallback_parse(raw_text)

    articles = []
    for block in blocks:
        article = _parse_single_block(block.strip())
        if article:
            articles.append(article)

    logger.info(f"Successfully parsed {len(articles)} articles from structured output.")
    return articles


def _parse_single_block(block_text):
    """단일 기사 블록을 dict로 변환"""
    article = {}
    lines = block_text.split("\n")
    
    current_field = None
    current_value_lines = []

    for line in lines:
        # KEY: VALUE 패턴 감지
        match = re.match(r'^([A-Z_]+):\s*(.*)', line)
        if match:
            # 이전 필드 저장
            if current_field:
                _store_field(article, current_field, "\n".join(current_value_lines).strip())
            
            current_field = match.group(1)
            current_value_lines = [match.group(2)]
        else:
            # 멀티라인 값 (CONTENT 등)
            if current_field:
                current_value_lines.append(line)

    # 마지막 필드 저장
    if current_field:
        _store_field(article, current_field, "\n".join(current_value_lines).strip())

    # 후처리: 필수 필드 검증 및 보완
    article = _post_process(article)
    
    if not article.get("eng_title"):
        logger.warning("Skipping article block: missing eng_title")
        return None
    
    return article


def _store_field(article, field_name, value):
    """필드명을 매핑하여 article dict에 저장"""
    mapped_key = FIELD_MAP.get(field_name)
    if not mapped_key:
        return

    # 키워드 필드는 리스트로 변환
    if "keywords" in mapped_key:
        value = [k.strip() for k in value.split(",") if k.strip()]
    
    # 요약 필드가 여러 줄이면 리스트로
    if mapped_key == "kor_summary" and "\n" in value:
        value = [line.strip().lstrip("- ").lstrip("· ") for line in value.split("\n") if line.strip()]
    
    article[mapped_key] = value


def _post_process(article):
    """기사 데이터 후처리: 카테고리/클러스터 검증 및 기본값 보충"""
    
    # 1. 카테고리 정규화
    cat = article.get("category", "ai-models").lower().replace(" ", "-")
    if cat not in VALID_CATEGORIES:
        # 유사어 매칭 또는 기본값
        if "chip" in cat or "gpu" in cat or "cpu" in cat: cat = "gpu-chips"
        elif "model" in cat or "llm" in cat: cat = "ai-models"
        elif "tool" in cat: cat = "ai-tools"
        elif "game" in cat: cat = "game-optimization"
        elif "guide" in cat: cat = "tutorials"
        else: cat = "ai-models"
    article["category"] = cat
    
    # 2. 클러스터 정규화 및 매핑
    cluster = article.get("cluster", "").lower().replace(" ", "-")
    if cluster not in VALID_CLUSTERS:
        # 카테고리 기반 자동 매핑 (강력한 신뢰도)
        cluster = CLUSTER_MAP.get(cat, "ai-models-tools")
    article["cluster"] = cluster
    
    # kor_summary가 문자열이면 리스트로 변환
    if isinstance(article.get("kor_summary"), str):
        article["kor_summary"] = [article["kor_summary"]]
    
    # 빈 필드 기본값
    if not article.get("eng_keywords"): article["eng_keywords"] = []
    if not article.get("kor_keywords"): article["kor_keywords"] = []
    if not article.get("kor_summary"): article["kor_summary"] = []
    if not article.get("eng_summary"): article["eng_summary"] = article.get("eng_title", "")
    
    return article


def _fallback_parse(raw_text):
    """구분자가 없는 경우의 폴백: JSON 블록 탐색"""
    # JSON 배열 시도
    json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, list):
                return [_post_process(item) for item in data]
        except:
            pass
    
    # 단일 JSON 객체 시도
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return [_post_process(data)]
        except:
            pass

    logger.error("Fallback parsing also failed. No parseable structure found.")
    return []


def parse_editorial_markdown(raw_text, category="ai-models"):
    """
    모드 A 전용: NotebookLM이 생성한 마크다운 사설을 단일 기사 dict로 변환.
    
    Args:
        raw_text: NotebookLM 출력 마크다운 텍스트
        category: 이 사설이 속한 카테고리 슬러그
    
    Returns:
        dict: create_hugo_post()에 투입 가능한 기사 데이터
    """
    if not raw_text or len(raw_text) < 200:
        logger.error("Editorial text too short or empty.")
        return None

    lines = raw_text.strip().split("\n")
    
    # 제목 추출: 첫 번째 # 라인
    title = "Megatrend Analysis"
    for line in lines:
        if line.startswith("#"):
            title = re.sub(r'^#+\s*', '', line).strip()
            # [심층 사설] 같은 접두사 제거
            title = re.sub(r'^\[.*?\]\s*', '', title).strip()
            break
    
    # 본문: 제목 라인 이후 전체
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    
    # 첫 문단을 설명으로 사용
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.startswith("#")]
    description = paragraphs[0][:200] + "..." if paragraphs else title
    
    article = {
        "kor_title": title,
        "kor_description": description,
        "kor_summary": [description[:100]],
        "kor_keywords": [category, "메가트렌드", "심층분석"],
        "kor_content": body,
        "kor_analysis_title": "심층 분석",
        "kor_insight_title": "에디터 인사이트",
        "kor_insight": "",  # 사설 자체가 인사이트이므로 비워둠
        "category": category,
        "cluster": CLUSTER_MAP.get(category, "ai-models-tools"),
        "image_prompt_core": f"Abstract futuristic {category} technology concept",
        "featured": True,
    }
    
    return article


# ===== 테스트용 =====
if __name__ == "__main__":
    sample = """
---ARTICLE_START---
ID: 1
ENG_TITLE: NVIDIA Blackwell GPU Sets New AI Training Records
KOR_TITLE: 엔비디아 블랙웰 GPU, AI 학습 신기록 수립
CATEGORY: gpu-chips
ENG_SUMMARY: NVIDIA's Blackwell architecture achieves unprecedented performance in MLPerf benchmarks.
KOR_SUMMARY:
- 블랙웰 아키텍처가 MLPerf 벤치마크에서 전례 없는 성능을 기록했다
- 경쟁사 AMD의 MI300X 대비 40% 이상의 성능 우위를 확보
- AI 학습 비용 절감에 실질적으로 기여할 수 있는 수준
ENG_CONTENT: ## Performance Analysis
The Blackwell architecture represents a significant leap...
KEYWORDS_EN: NVIDIA, Blackwell, MLPerf
KEYWORDS_KR: 엔비디아, 블랙웰, 벤치마크
IMAGE_PROMPT: NVIDIA Blackwell GPU chip glowing with blue neon light
---ARTICLE_END---
"""
    results = parse_structured_articles(sample)
    for r in results:
        print(json.dumps(r, indent=2, ensure_ascii=False))
