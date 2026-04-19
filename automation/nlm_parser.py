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
    "ENGLISH_TITLE": "eng_title",
    "KOR_TITLE": "kor_title",
    "KOREAN_TITLE": "kor_title",
    "TITLE": "eng_title",
    "CLUSTER": "cluster",
    "CATEGORY": "category",
    "ENG_SUMMARY": "eng_summary",
    "ENGLISH_SUMMARY": "eng_summary",
    "KOR_SUMMARY": "kor_summary",
    "KOREAN_SUMMARY": "kor_summary",
    "SUMMARY": "eng_summary",
    "ENG_CONTENT": "eng_content",
    "ENGLISH_CONTENT": "eng_content",
    "ENGLISH_CONTENT_SYNTHESIS": "eng_content",
    "SYNTHESIS": "eng_content",
    "KOR_CONTENT": "kor_content",
    "KOREAN_CONTENT": "kor_content",
    "CONTENT": "eng_content",
    "KOR_INSIGHT": "kor_insight",
    "KOREAN_INSIGHT": "kor_insight",
    "KEYWORDS_EN": "eng_keywords",
    "ENGLISH_KEYWORDS": "eng_keywords",
    "KEYWORDS_KR": "kor_keywords",
    "KOREAN_KEYWORDS": "kor_keywords",
    "KEYWORDS": "eng_keywords",
    "IMAGE_PROMPT": "image_prompt_core",
    "ORIGINAL_IMAGE": "original_image",
    "ORIGINAL_IMAGE_URL": "original_image",
}

# [V4.0] 초정예 AI 중심 대분류
VALID_CLUSTERS = ["ai", "hardware", "insights"]

# [V4.0] 초정예 중분류
VALID_CATEGORIES = ["models", "apps", "high-end", "chips", "analysis", "guide"]

# 카테고리 -> 클러스터 매핑
CLUSTER_MAP = {
    "models": "ai", "apps": "ai",
    "high-end": "hardware", "chips": "hardware",
    "analysis": "insights", "guide": "insights"
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

    # [V3.2] 구분자 인식 극강화: 대시, 볼드, 불렛 포인트 등 모든 변종 대응
    # 예: ---ARTICLE_START---, * **ARTICLE_START**, ARTICLE_START: 등
    pattern = r'(?i)(?:---|\*?\s*\*\*?)?ARTICLE_START(?:---|\*\*?)?[:：]?\s*(.*?)(?:---|\*?\s*\*\*?)?ARTICLE_END(?:---|\*\*?)?[:：]?'
    blocks = re.findall(pattern, raw_text, re.DOTALL)

    if not blocks:
        # [V2.4] 더 강력한 폴백: ID와 숫자 사이에 어떤 문자가 오더라도 인식 (예: ID [순번]: 1)
        logger.warning("No ARTICLE_START/END found. Trying ID-based splitting...")
        id_pattern = r'(?i)(?:[*#]|\d+\.)?\s*(?:\*\*)?ID[^0-9\n]*\d+'
        blocks = re.split(id_pattern, raw_text)
        
        if len(blocks) > 1:
            id_matches = re.findall(id_pattern, raw_text)
            blocks = [id_matches[i] + blocks[i+1] for i in range(len(id_matches))]
        else:
            # [V3.3] 최후의 보루: 구분자도 ID도 없지만 텍스트가 길다면 전체를 하나의 기사로 취급
            logger.warning("No structure found. Treating entire file as one article block.")
            blocks = [raw_text]

    articles = []
    for i, block in enumerate(blocks):
        article = _parse_single_block(block.strip()) or {}
        
        # [V3.3] 필드 추출 실패 시 긴 텍스트를 통째로 콘텐츠로 할당
        if len(block.strip()) > 500 and not article.get('eng_content') and not article.get('kor_content'):
            # 한글 포함 여부로 필드 결정
            if any('\uac00' <= char <= '\ud7a3' for char in block):
                article['kor_content'] = block.strip()
                if not article.get('kor_title'): article['kor_title'] = f"심층 분석 리포트 #{i}"
            else:
                article['eng_content'] = block.strip()
                if not article.get('eng_title'): article['eng_title'] = f"Intelligence Report #{i}"

        # [V3.9] 제목이 끝까지 없는 경우: ID가 있다면 사용, 없으면 순번 사용
        if not article.get('eng_title') and not article.get('kor_title'):
            article_id = article.get('id', str(i))
            article['eng_title'] = f"Article {article_id}"
            
        articles.append(article)

    logger.info(f"Successfully parsed {len(articles)} articles.")
    return articles


def _parse_single_block(block_text):
    """단일 기사 블록을 dict로 변환"""
    article = {}
    lines = block_text.split("\n")
    
    current_field = None
    current_value_lines = []

    for line in lines:
        # [V3.16] 숫자형 불렛(1. 2. ) 및 마크다운 기호 혼합 대응
        # 예: 7. **KOR_SUMMARY**: -> KOR_SUMMARY 매핑용
        match = re.search(r'(?:[*#\s\d.-]*)(?:\*\*|__)?([A-Za-z\s_]{2,})(?:\*\*|__)?[:：]?\s*(.*)', line)
        
        found_key = None
        if match:
            potential_field = match.group(1).upper().replace(" ", "").replace("_", "")
            sorted_keys = sorted(FIELD_MAP.keys(), key=len, reverse=True)
            for k in sorted_keys:
                normalized_k = k.upper().replace(" ", "").replace("_", "")
                if normalized_k == potential_field:
                    found_key = k
                    break
        
        if found_key:
            if current_field:
                _store_field(article, current_field, "\n".join(current_value_lines).strip())
            
            current_field = found_key
            val = match.group(2).strip()
            current_value_lines = [val] if val else []
            continue

        # [V3.20] 잡음 제거 로직 완화: 요약 리스트(1. 2.)가 무시되지 않도록 수정
        # 기존: if re.match(r'^\s*(?:#+\s*)?\d+\.\s+[A-Za-z가-힣]', line): 
        # 이제 필드명 후보가 아님이 확실하고, 단순 번호만 있는 경우 등 아주 제한적으로만 스킵
        if re.match(r'^\s*(?:#+\s*)?\d+\.\s*$', line):
            continue

        # 멀티라인 값 (CONTENT, SUMMARY 등)
        if current_field:
            current_value_lines.append(line)

    # 마지막 필드 저장
    if current_field:
        _store_field(article, current_field, "\n".join(current_value_lines).strip())

    # 후처리: 필수 필드 검증 및 보완
    article = _post_process(article)
    
    if not article.get("eng_title") and not article.get("kor_title"):
        logger.warning("Skipping article block: missing both titles")
        return None
    
    return article


def _store_field(article, field_name, value):
    """필드명을 매핑하여 article dict에 저장"""
    mapped_key = FIELD_MAP.get(field_name)
    if not mapped_key:
        return

    # [V3.7] 마크다운 볼드(**) 제거 및 공백 정리
    value = value.replace("**", "").strip()
    
    # [V3.7] 불필요한 공정용 마커(Headings) 제거 로직
    # NLM이 소제목으로 남기는 쓰레기 텍스트들
    noise_patterns = [
        r"(?i)^###?\s*Deep-Dive.*",
        r"(?i)^###?\s*Professional Insight.*",
        r"(?i)^###?\s*Section\s*\d+.*",
        r"(?i)^###?\s*Step\s*\d+.*",
        r"(?i)^###?\s*Conclusion.*",
        r"(?i)^###?\s*Analysis.*"
    ]
    for pattern in noise_patterns:
        value = re.sub(pattern, "", value, flags=re.MULTILINE).strip()

    # 키워드 필드는 리스트로 변환
    if "keywords" in mapped_key:
        value = [k.replace("**", "").strip().strip("*").strip().rstrip(".") for k in value.split(",") if k.strip()]
    
    # 요약 필드가 여러 줄이면 리스트로
    if mapped_key == "kor_summary" and "\n" in value:
        value = [line.strip().lstrip("- ").lstrip("· ") for line in value.split("\n") if line.strip()]
    
    article[mapped_key] = value


def _post_process(article):
    """기사 데이터 후처리: 카테고리/클러스터 검증 및 기본값 보충"""
    
    # [V3.17] 요약 항목 불렛 중복 방지 (기호 제거)
    def clean_summary(summary_list):
        if not summary_list: return []
        if isinstance(summary_list, str): summary_list = [summary_list]
        cleaned = []
        for s in summary_list:
            s = re.sub(r'^\s*[*•\d.-]+\s*', '', s).strip()
            if s: cleaned.append(s)
        return cleaned

    article["kor_summary"] = clean_summary(article.get("kor_summary", []))
    article["eng_summary"] = clean_summary(article.get("eng_summary", []))
    
    # [V3.18] description은 문자열이어야 함
    article["kor_description"] = article.get("kor_summary", [""])[0] if article.get("kor_summary") else ""
    article["eng_description"] = article.get("eng_summary", [""])[0] if article.get("eng_summary") else ""

    # 1. 카테고리 정규화 (중분류) - V4.1 초정예 매핑 (제목/본문 분석 추가)
    cat_raw = article.get("category", "models").lower().replace(" ", "-")
    content_text = (article.get("title", "") + " " + article.get("kor_description", "")).lower()
    
    cat = "models" # 기본값
    
    # [V4.1] 강력한 키워드 기반 강제 분류
    # A. 인사이트 (비교/분석, 가이드)
    if any(k in content_text for k in ["bench", "compare", "vs", "analysis", "effic", "비교", "분석", "성능"]): cat = "analysis"
    elif any(k in content_text for k in ["guide", "tutorial", "how", "tip", "dev", "가이드", "팁", "방법"]): cat = "guide"
    
    # B. 하드웨어 (하이엔드 PC, 반도체)
    elif any(k in content_text for k in ["9800", "5080", "build", "case", "cooler", "desktop", "데스크탑", "조립"]): cat = "high-end"
    elif any(k in content_text for k in ["chip", "gpu", "tsmc", "intel", "nvidia", "accel", "semicon", "fab", "반도체", "칩"]): cat = "chips"
    
    # C. AI (활용/도구, 모델)
    elif any(k in content_text for k in ["app", "workflow", "harvester", "tool", "auto", "productivity", "툴", "활용", "자동화"]): cat = "apps"
    elif any(k in content_text for k in ["model", "llm", "gpt", "gemini", "claude", "ai", "openai", "deepmind", "모델"]): cat = "models"
    
    # 카테고리가 명시적으로 지정되었으나 위에서 안 걸린 경우 (ID 보정)
    if cat == "models" and any(k in cat_raw for k in ["bench", "compare"]): cat = "analysis"
    elif cat == "models" and any(k in cat_raw for k in ["guide", "tutorial"]): cat = "guide"
    elif cat == "models" and any(k in cat_raw for k in ["chip", "gpu", "tsmc", "intel", "nvidia", "accel", "semicon"]): cat = "chips"
    elif cat == "models" and any(k in cat_raw for k in ["build", "pc"]): cat = "high-end"
    elif cat == "models" and any(k in cat_raw for k in ["app", "tool", "work"]): cat = "apps"

    article["category"] = cat
    
    # 2. 클러스터 정규화 및 매핑 (대분류)
    cluster = article.get("cluster", "").lower().replace(" ", "-")
    if cluster not in VALID_CLUSTERS:
        cluster = CLUSTER_MAP.get(cat, "ai")
    article["cluster"] = cluster
    
    # 3. 제목 상호 보완 (Untitled 방지)
    if not article.get("eng_title") and article.get("kor_title"):
        article["eng_title"] = article["kor_title"]
    if not article.get("kor_title") and article.get("eng_title"):
        article["kor_title"] = article["eng_title"]
    
    # [V3.13] 제목 누락 시 본문 첫 줄 추출
    if not article.get("eng_title") and article.get("eng_content"):
        first_line = article["eng_content"].split("\n")[0].strip().strip("#").strip()
        if len(first_line) > 10: article["eng_title"] = first_line[:100]
        
    if not article.get("kor_title") and article.get("kor_content"):
        first_line = article["kor_content"].split("\n")[0].strip().strip("#").strip()
        if len(first_line) > 10: article["kor_title"] = first_line[:100]

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

    # [V3.15] 구조적 마커 및 불필요한 필드명 제거
    raw_content = re.sub(r'---ARTICLE_(?:START|END)---', '', raw_text)
    raw_content = re.sub(r'(?i)\*\*ID:\*\*\s*\d+', '', raw_content)
    raw_content = re.sub(r'(?i)\*\*(?:KOR_CONTENT|KOREAN_CONTENT|ENG_CONTENT|ENGLISH_CONTENT|KOR_INSIGHT|IMAGE_PROMPT)\*\*[:：]?', '', raw_content)
    
    lines = raw_content.strip().split("\n")
    
    # 제목 추출: 첫 번째 # 라인
    title = "Megatrend Analysis"
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            title = re.sub(r'^#+\s*', '', line).strip()
            # [심층 사설] 같은 접두사 제거
            title = re.sub(r'^\[.*?\]\s*', '', title).strip()
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
        "cluster": CLUSTER_MAP.get(category, "ai"),
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
