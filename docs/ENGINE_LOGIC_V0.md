# 🛠️ LEGO-SIA V0: ENGINE CORE LOGIC (Technical Deep-Dive)

> **문서 상태**: V0.2 (High-Density & Parallelized)  
> **목적**: 수집, 편집, 한글화 로직의 전체 구조 분석 및 개선 포인트 식별

---

## 🏗️ 1단계: 수집 로직 (The Harvester)
**파일**: `automation/news_harvester.py`

### 1.1 하이브리드 수집 전략
*   **RSS (The Net)**: 미리 지정된 `rss_feeds.json` 화이트리스트를 통해 ITWorld, Reuters 등 신뢰도 높은 소스에서 1차 수확.
*   **API Sniper (The Sniper)**: 수량이 부족한 카테고리에 대해 `NewsAPI`, `GNews` 등을 사용하여 실시간 키워드 공격(Sniping). 7일 이내의 뉴스만 타겟팅함.

### 1.2 지능형 분류 및 필터링 (V0.2 핵심 업데이트)
*   **Rule-based 분류**: 제목과 설명 내의 키워드(GPU, AI, Unreal 등)를 기반으로 8개 카테고리로 자동 배정.
*   **[개선] 분량 필터링**: `len(content_summary) < 150`인 경우 '단신'으로 간주하여 과감히 탈락. (읽을 맛 안 나는 텍스트 원천 차단)
*   **Token Pre-Reduction**: 소스 텍스트에서 가장 영양가 있는 핵심 5문장만 추출하여 AI에게 전달 (비용 및 토큰 효율화).

---

## ✒️ 2단계: 편집 로직 (The Editor - Synthesis)
**파일**: `automation/ai_news_editor.py` (Step 1)

### 2.1 영문 스타일 가이드
*   **Persona**: 단순 기자가 아닌 'Strategic Analyst'이자 'Senior Technical Journalist'.
*   **Synthesis**: 여러 소스에서 받은 정보를 조합하여 하나의 완결된 영문 리포트로 재구성.
*   **[V0.2] 고밀도 규칙 (High-Density)**: 
    *   중제목(Subheading)만 나열하지 말 것.
    *   각 섹션 아래에는 **최소 4~5문장 이상의 상세 서술**이 포함되어야 함.
    *   단순 사실 나열(What)보다는 **이유(Why)와 방법(How)**을 심도 있게 다룸.

### 2.2 스코어링 (Reviewer)
*   `ai_reviewer.py`를 통해 발행 전 최종 검수.
*   전략적 가치, 톤의 냉철함, E-E-A-T 등을 1~10점으로 평가하여 7점 미만은 자동 폐기.

---

## 🇰🇷 3단계: 한글화 로직 (The Localization)
**파일**: `automation/ai_news_editor.py` (Step 2)

### 3.1 용어 사전 (Glossary) 강제 매핑
*   `_apply_glossary` 함수를 통해 AI가 흔히 실수하는 한국어 표현을 강제 치환.
    *   예: `Anthropic` → `앤트로픽(Anthropic)`, `Foundry` → `파운드리(위탁 생산)`
*   AI만의 말투(~입니다, ~해요 등)를 제거하고 전문적인 문어체로 고정.

### 3.2 인사이트 추출 및 SEO 최적화
*   단순 번역이 아닌 **'한국 시장에 주는 시사점'**을 별도 세션으로 추출.
*   JSON 구조로 분리하여 Hugo Frontmatter에 태그, 클러스터, 설명글을 자동으로 박아 넣음.

---

## 📈 개선 및 튜닝 포인트 (Next for User)

1.  **수집**: 현재 키워드 풀인 `self.keyword_pools`를 수시로 업데이트하여 트렌드 변화에 대응 가능.
2.  **편집**: `localize_prompt` 내의 `CONTENT DENSITY` 규칙 숫자를 조정하여 기사 길이를 조절 가능 (현재 4~5문장).
3.  **한글화**: `GLOSSARY` 딕셔너리에 새로운 전문 용어를 지속적으로 추가하여 번역 품질 우상향 유도.

---
**기능 요약 도표**
| 단계 | 핵심 컴포넌트 | 모델 | 주요 파라미터 |
| :--- | :--- | :--- | :--- |
| 수집 | `NewsHarvester` | N/A | `limit_per_cat`, `days=7` |
| 편집 | `NewsEditor (Step 1)` | Gemma 4 | `Synthesis Prompt` |
| 번역 | `NewsEditor (Step 2)` | Gemma 4 | `Glossary`, `Insight Extract` |
| 검수 | `EditorInChief` | Gemma 4 | `Score >= 7.0` |
