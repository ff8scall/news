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
    "TITLE_KR": "kor_title",
    "TITLE_EN": "eng_title",
    "TITLE": "eng_title",
    "CLUSTER": "cluster",
    "CATEGORY": "category",
    "ENG_SUMMARY": "eng_summary",
    "ENGLISH_SUMMARY": "eng_summary",
    "KOR_SUMMARY": "kor_summary",
    "KOREAN_SUMMARY": "kor_summary",
    "SUMMARY_KR": "kor_summary",
    "SUMMARY_EN": "eng_summary",
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
    "INSIGHT_KR": "kor_insight",
    "INSIGHTS": "kor_insight",
    "INSIGHT": "kor_insight",
    "CORE_INSIGHT": "kor_insight",
    "KEYWORDS_EN": "eng_keywords",
    "ENGLISH_KEYWORDS": "eng_keywords",
    "KEYWORDS_KR": "kor_keywords",
    "KOREAN_KEYWORDS": "kor_keywords",
    "KEYWORDS": "eng_keywords",
    "IMAGE_PROMPT": "image_prompt_core",
    "ORIGINAL_IMAGE": "original_image",
    "ORIGINAL_IMAGE_URL": "original_image",
    "CLUSTERCATEGORY": "cluster",
    "CLUSTER/CATEGORY": "cluster",
    "CATEGORY/CLUSTER": "cluster",
}

# [V5.0] 신규 4대 대메뉴 체제 및 자동 분류 키워드 맵
VALID_CLUSTERS = ["ai", "hardware", "insights", "markets"]

CLUSTER_MAP = {
    "ai": [
        "모델", "llm", "gpt", "gemini", "claude", "에이전트", "ai", "model", "agent", 
        "software", "챗봇", "인공지능", "딥러닝", "머신러닝", "neural", "open source", "llama", "huggingface"
    ],
    "hardware": [
        "반도체", "칩", "gpu", "cpu", "생산", "공정", "하드웨어", "chip", "hardware", 
        "infrastructure", "데스크탑", "파운드리", "tsmc", "nvidia", "intel", "amd", "server", "data center"
    ],
    "insights": [
        "전략", "분석", "미래", "전망", "혁신", "심층", "insight", "strategy", "trend", 
        "보고서", "트렌드", "리서치", "가이드", "튜토리얼", "사례연구"
    ],
    "markets": [
        "ipo", "투자", "펀딩", "인수", "합병", "매출", "실적", "vc", "시장 규모", 
        "business", "market", "startup", "비즈니스", "수익", "주식", "경제", "나스닥", "테크 거물"
    ]
}


def parse_structured_articles(raw_text):
    """
    모드 B 전용: ---ARTICLE_START--- / ---ARTICLE_END--- 구분자 기반 파싱.
    """
    if not raw_text:
        logger.error("Empty text received for parsing.")
        return []

    pattern = r'(?i)(?:---|\*?\s*\*\*?)?ARTICLE_START(?:---|\*\*?)?[:：]?\s*(.*?)(?:---|\*?\s*\*\*?)?ARTICLE_END(?:---|\*\*?)?[:：]?'
    blocks = re.findall(pattern, raw_text, re.DOTALL)

    if not blocks:
        logger.warning("No ARTICLE_START/END found. Trying ID-based splitting...")
        id_pattern = r'(?i)(?:[*#]|\d+\.)?\s*(?:\*\*)?ID[^0-9\n]*\d+'
        blocks = re.split(id_pattern, raw_text)
        
        if len(blocks) > 1:
            id_matches = re.findall(id_pattern, raw_text)
            blocks = [id_matches[i] + blocks[i+1] for i in range(len(id_matches))]
        else:
            logger.warning("No structure found. Treating entire file as one article block.")
            blocks = [raw_text]

    articles = []
    for i, block in enumerate(blocks):
        article = _parse_single_block(block.strip()) or {}
        
        if len(block.strip()) > 500 and not article.get('eng_content') and not article.get('kor_content'):
            if any('\uac00' <= char <= '\ud7a3' for char in block):
                article['kor_content'] = block.strip()
                if not article.get('kor_title'): article['kor_title'] = f"심층 분석 리포트 #{i}"
            else:
                article['eng_content'] = block.strip()
                if not article.get('eng_title'): article['eng_title'] = f"Intelligence Report #{i}"

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
        # 필드 추출 정규식: 시작 부분부터 매칭하며, 필드명 앞뒤의 마크다운 기호를 유연하게 처리
        # [V12.1] 콜론이 없거나 마크다운 헤더(#) 형태인 경우에도 필드명(FIELD_MAP)이면 매칭되도록 유연화
        # [V12.3] 필드 추출 정규식: 하이픈(-) 및 슬래시(/) 등 필드명 특수문자 대응 강화
        match = re.match(r'(?i)^\s*(?:\d+[\.)]\s*)?[#\*\*_\[]*([A-Z\s/_-]{2,})[#\*\*_\]]*\s*[:：]?\s*(.*)', line)
        
        found_key = None
        if match:
            potential_field = match.group(1).upper().replace(" ", "").replace("_", "")
            # 매칭된 텍스트가 실제로 FIELD_MAP에 존재하는 키의 변형인지 검증
            sorted_keys = sorted(FIELD_MAP.keys(), key=len, reverse=True)
            for k in sorted_keys:
                normalized_k = k.upper().replace(" ", "").replace("_", "")
                if normalized_k == potential_field:
                    found_key = k
                    break
            
            # [V12.0] 콜론이 없는데 FIELD_MAP에도 없는 일반 텍스트면 매칭 무효화 (오탐 방지)
            if found_key and ":" not in line and "：" not in line and potential_field not in [k.upper().replace(" ", "").replace("_", "") for k in FIELD_MAP.keys()]:
                found_key = None
        
        if found_key:
            if current_field:
                _store_field(article, current_field, "\n".join(current_value_lines).strip())
            
            val = match.group(2).strip()
            # [V11.5] 필드 시작 줄에 ## 헤더와 한글이 포함된 경우 제목으로 우선 채택
            if found_key.upper() in ["KOR_CONTENT", "KOREAN_CONTENT", "CONTENT"] and not article.get("kor_title"):
                # 헤더 앞의 ** 등 노이즈 제거 후 확인
                clean_val = val.strip("*").strip("_").strip()
                if re.match(r'^\s*##\s+', clean_val) and any('\uac00' <= char <= '\ud7a3' for char in clean_val):
                    article["kor_title"] = clean_val.strip("#").strip()

            current_field = found_key
            current_value_lines = [val] if val else []
            continue
        
        # 제목 필드는 메타데이터로 간주하여 ## 등의 내용이 붙지 않게 함
        METADATA_FIELDS = ["TITLE", "ENG_TITLE", "KOR_TITLE", "KOREAN_TITLE", "CLUSTER", "CATEGORY", "ID", "KOR_SUMMARY"]
        if not current_field or current_field in METADATA_FIELDS or current_field == "SYNTHESIS":
            if re.match(r'^\s*##\s+', line) and any('\uac00' <= char <= '\ud7a3' for char in line):
                if current_field:
                    _store_field(article, current_field, "\n".join(current_value_lines).strip())
                if not article.get("kor_title"):
                    article["kor_title"] = line.strip("#").strip()
                current_field = "KOR_CONTENT"
                current_value_lines = [line]
                continue
        elif any(k in (current_field or "").upper() for k in ["CONTENT", "INSIGHT", "SYNTHESIS"]):
            # 이미 본문/인사이트 파싱 중인데 ## 헤더를 만난 경우 필드를 초기화하지 않고 제목이 없을 때만 추출
            if re.match(r'^\s*##\s+', line) and any('\uac00' <= char <= '\ud7a3' for char in line):
                if not article.get("kor_title"):
                    article["kor_title"] = line.strip("#").strip()

        if re.match(r'^\s*(?:#+\s*)?\d+\.\s*$', line): continue
        if current_field:
            current_value_lines.append(line)

    if current_field:
        _store_field(article, current_field, "\n".join(current_value_lines).strip())

    return _post_process(article) if article else None


def _store_field(article, field_name, value):
    """필드명을 매핑하여 article dict에 저장"""
    mapped_key = FIELD_MAP.get(field_name)
    if not mapped_key: return

    value = value.replace("**", "").strip()

    if mapped_key in ["kor_title", "eng_title"]:
        # 제목 정제: CLUSTER / CATEGORY 등 NLM이 덧붙이는 모든 패턴 제거 (멀티라인 대응)
        clean_patterns = [
            r'(?im)\s*[\[(]?\s*(?:CLUSTER|CATEGORY|CLUSTER/CATEGORY|CLUSTER\s*/\s*CATEGORY)[:：].*?[\])]?\s*$',
            r'(?im)\s*\|\s*(?:CLUSTER|CATEGORY).*?$',
            r'(?im)\s*CLUSTER / CATEGORY.*$'
        ]
        for p in clean_patterns:
            value = re.sub(p, '', value).strip()
    
    if mapped_key == "kor_content":
        value = re.sub(r'^##\s+', '### ', value, flags=re.MULTILINE)
        val_lines = value.split("\n")
        new_lines = []
        for i, line in enumerate(val_lines):
            stripped_line = line.strip().replace("#", "").strip()
            if i < 3 and re.match(r'^(상세|심층|전략적|기술적)\s*(분석|리포트|Deep-Dive)$', stripped_line): continue
            new_lines.append(line)
        value = "\n".join(new_lines).strip()

    noise_patterns = [r"(?i)^###?\s*Deep-Dive\s*$", r"(?i)^###?\s*Professional Insight\s*$", r"(?i)^###?\s*Section\s*\d+\s*$", r"(?i)^###?\s*Step\s*\d+\s*$", r"(?i)^###?\s*Conclusion\s*$"]
    for pattern in noise_patterns:
        value = re.sub(pattern, "", value, flags=re.MULTILINE).strip()

    if "keywords" in mapped_key:
        # [V12.3] 태그 길이 제한 (최대 40자) 및 비정상 텍스트 필터링 (빌드 정지 방지)
        raw_keywords = [k.replace("**", "").strip().strip("*").strip().rstrip(".") for k in value.split(",") if k.strip()]
        value = []
        for kw in raw_keywords:
            if 1 < len(kw) < 100: # 100자 이상의 텍스트는 오탐으로 간주하여 제외
                value.append(kw[:40]) # 혹시 모를 상황 대비 40자로 최종 절단
    if mapped_key == "kor_summary" and "\n" in value:
        value = [line.strip().lstrip("- ").lstrip("· ") for line in value.split("\n") if line.strip()]
    
    article[mapped_key] = value


def _post_process(article):
    """기사 데이터 후처리: 클러스터 분류 및 기본값 보충 (V5.0 4대 체계)"""
    
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
    
    if not article.get("kor_summary") and article.get("kor_content"):
        paragraphs = [p.strip() for p in article["kor_content"].split("\n") if p.strip() and not p.startswith("#")]
        if paragraphs:
            summary = paragraphs[0][:600] + "..." if len(paragraphs[0]) > 600 else paragraphs[0]
            article["kor_summary"] = [summary]

    if not article.get("eng_summary") and article.get("eng_content"):
        paragraphs = [p.strip() for p in article["eng_content"].split("\n") if p.strip() and not p.startswith("#")]
        if paragraphs:
            summary = paragraphs[0][:600] + "..." if len(paragraphs[0]) > 600 else paragraphs[0]
            article["eng_summary"] = [summary]

    article["kor_description"] = article.get("kor_summary", [""])[0] if article.get("kor_summary") else ""
    article["eng_description"] = article.get("eng_summary", [""])[0] if article.get("eng_summary") else ""

    # 1. 클러스터 자동 분류 (V1.1 고도화 로직)
    content_text = (article.get("kor_title", "") + " " + article.get("kor_description", "") + " " + (article.get("kor_content", "") or "")).lower()
    
    # 기본값 설정
    detected_cluster = article.get("cluster", "").lower().replace(" ", "-")
    if detected_cluster not in VALID_CLUSTERS:
        detected_cluster = "ai" # 기본값
        
        # 키워드 점수 기반 재분류
        scores = {c: 0 for c in VALID_CLUSTERS}
        for cluster_id, keywords in CLUSTER_MAP.items():
            for kw in keywords:
                if kw in content_text:
                    scores[cluster_id] += 1
        
        # 가장 높은 점수를 받은 클러스터 선택
        max_score = 0
        for cluster_id, score in scores.items():
            if score > max_score:
                max_score = score
                detected_cluster = cluster_id

    article["cluster"] = detected_cluster
    if "category" in article: del article["category"]
    
    # 2. 제목 복구: 본문(Content) 또는 인사이트(Insight/Synthesis/Summary)에서 후보 탐색
    has_kor_text = (article.get("kor_content") and len(article["kor_content"]) > 10) or \
                   (article.get("kor_insight") and len(article.get("kor_insight", "")) > 10) or \
                   (article.get("synthesis") and len(article.get("synthesis", "")) > 10) or \
                   (article.get("kor_summary") and len(str(article.get("kor_summary", ""))) > 10)
    
    if (not article.get("kor_title") or article.get("kor_title").startswith("심층 분석") or article.get("kor_title") == article.get("eng_title")) and has_kor_text:
        # 소스 우선 순위: 한글 본문 > 인사이트 > 요약 > 영문 본문(파싱 오류 대비)
        source_candidates = [
            article.get("kor_content"), 
            article.get("kor_insight"), 
            article.get("synthesis"), 
            "\n".join(article["kor_summary"]) if isinstance(article.get("kor_summary"), list) else article.get("kor_summary"),
            article.get("eng_content") # [V12.0] 파싱 오류로 한글이 영문 필드에 들어간 경우 대응
        ]
        
        for source_text in source_candidates:
            if not source_text or len(source_text) < 10: continue
            
            content_lines = [l.strip() for l in source_text.split("\n") if l.strip()]
            found = False
            for line in content_lines[:5]: # 상위 5줄까지 탐색 범위 확장
                clean_line = line.strip("#").strip("*").strip()
                # 문장 단위로 분리하여 첫 문장 추출
                first_sentence = re.split(r'[.!?]\s+', clean_line)[0]
                # 한글 포함 여부 및 유의미한 길이 확인
                if any('\uac00' <= char <= '\ud7a3' for char in first_sentence) and len(first_sentence) > 5:
                    article["kor_title"] = first_sentence[:80].strip() + "..." if len(first_sentence) > 80 else first_sentence.strip()
                    found = True
                    break
            if found: break

    # 3. 콘텐츠 보존: kor_content가 비어있는데 다른 한글 필드가 있다면 복구
    if not article.get("kor_content") or len(article["kor_content"]) < 20:
        if article.get("kor_insight"):
            article["kor_content"] = "## 주요 분석\n" + article["kor_insight"]
        elif article.get("kor_summary"):
            summary_text = "\n".join([f"* {s}" for s in article["kor_summary"]]) if isinstance(article["kor_summary"], list) else str(article["kor_summary"])
            article["kor_content"] = "## 요약 분석\n" + summary_text

    if not article.get("eng_title"):
        article["eng_title"] = f"Recovery: {article['kor_title']}" if article.get("kor_title") else f"Article {article.get('id', 'Unknown')}"
    if not article.get("kor_title") and article.get("eng_title"):
        article["kor_title"] = article.get("eng_title")
    
    if not article.get("eng_keywords"): article["eng_keywords"] = []
    if not article.get("kor_keywords"): article["kor_keywords"] = []
    if not article.get("kor_summary"): article["kor_summary"] = []
    if not article.get("eng_summary"): article["eng_summary"] = [article.get("eng_title", "")]
    
    return article


def _fallback_parse(raw_text):
    """구분자가 없는 경우의 폴백: JSON 블록 탐색"""
    json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if isinstance(data, list): return [_post_process(item) for item in data]
        except: pass
    
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return [_post_process(data)]
        except: pass
    return []


def parse_editorial_markdown(raw_text, category="ai-models"):
    """모드 A 전용: 마크다운 사설 → 단일 기사 dict"""
    if not raw_text or len(raw_text) < 200: return None
    raw_content = re.sub(r'---ARTICLE_(?:START|END)---', '', raw_text)
    raw_content = re.sub(r'(?i)\*\*ID:\*\*\s*\d+', '', raw_content)
    raw_content = re.sub(r'(?i)\*\*(?:KOR_CONTENT|KOREAN_CONTENT|ENG_CONTENT|ENGLISH_CONTENT|KOR_INSIGHT|IMAGE_PROMPT)\*\*[:：]?', '', raw_content)
    
    lines = raw_content.strip().split("\n")
    title = "Megatrend Analysis"
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            title = re.sub(r'^#+\s*', '', line).strip()
            body_start = i + 1
            break
    
    body = "\n".join(lines[body_start:]).strip()
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.startswith("#")]
    description = paragraphs[0][:200] + "..." if paragraphs else title
    
    return {
        "kor_title": title,
        "eng_title": f"Deep-Dive: {title}",
        "kor_content": body,
        "kor_description": description,
        "cluster": "insights",
        "tags": ["Analysis", "Trend", "Strategy"]
    }
