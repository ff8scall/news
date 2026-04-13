# 📜 LEGACY CORE RULES: 레고-시아 뉴스 엔진의 지성

> 본 문서는 V0로의 대전환 과정에서 보존해야 할 핵심 로직과 노하우를 정리한 문서입니다. 새로운 코드를 작성할 때 이 규칙들을 '영혼'처럼 주입해야 합니다.

## 1. 페르소나 및 작성 원칙 (Persona)
*   **Editor-in-Chief**: 냉소적이고 비판적이며, 단순한 뉴스를 넘어선 '전략적 가치'를 중요시함.
*   **Journalist**: "공부가 아닌 정보 습득"을 목적으로 함. 경어와 격식 있는 문체를 사용하되, AI 특유의 '신난 듯한' 투를 지양함.
*   **EEAT 강화**: 출처(Source Tiering)를 명시하고, 전문가의 시각에서 재해석된 '인사이트' 섹션을 반드시 포함함.

## 2. 필수 용어 사전 (Glossary)
오역 방지를 위해 강제로 치환해야 하는 핵심 용어들입니다:
*   **Anthropic** → 앤트로픽(Anthropic)
*   **NVIDIA** → 엔비디아(NVIDIA)
*   **Blackwell** → 블랙웰(Blackwell)
*   **HBM** → HBM(고대역폭 메모리)
*   **LLM** → LLM(대규모 언어 모델)
*   **Foundry** → 파운드리(위탁 생산)

## 3. 기사 생성 및 정제 포인트
*   **Scoring (1-10)**: 7점 이상의 기사만 발행하며, 5-7점 사이는 권위 있는 공식 뉴스 소스(`Reuters`, `TechCrunch` 등)인 경우에만 통과.
*   **JSON Schema**: 모든 결과물은 정규화된 JSON 형태여야 하며, `eng_content`와 `kor_content`가 1:1로 매칭되는지 확인함.
*   **Image Fallback**: 기사의 이미지가 깨졌거나 없을 경우, 반드시 카테고리별 전략 이미지로 대체하여 시각적 프리미엄을 유지함.

## 4. 수익화 및 SEO 전략
*   **CPC Focus**: GPU, 반도체, PC 하드웨어 기사는 구체적인 스펙 표를 포함하여 고관여 사용자의 머무는 시간을 늘림.
*   **How-to Focus**: 툴(Cursor, Copilot) 관련 기사는 "따라 하기만 하면 되는" 실무 튜토리얼로 자동 전환함.

---
**기록자**: Antigravity (AI Assistant)
