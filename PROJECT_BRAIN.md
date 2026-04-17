# 🧠 PROJECT BRAIN: 레고-시아 V0 (Genesis)

> **현재 시점**: 2026-04-14  
> **상태**: V0 초기화 완료 및 1차 대규모 콘텐츠 동기화 완료 (90:90 매칭)
> **슬로건**: "AI와 게임, 오직 트래픽과 가치에 집중한다."

## 🏛️ V0 확정 시스템 설계 (System Blueprint)

### 1. 콘텐츠 클러스터 (Taxonomy)
현재 사이트는 4개의 대분류(Cluster)와 8개의 소분류(Category)로 구성되어 있습니다.

| 대분류 (Cluster Slug) | 대분류 명 (UI) | 소분류 (Category Slug) | 소분류 명 (Display) |
| :--- | :--- | :--- | :--- |
| `ai-models-tools` | **AI** | `ai-models` | AI 모델 · 트렌드 |
| | | `ai-tools` | AI 도구 · 사용법 |
| `gpu-hardware` | **하드웨어** | `gpu-chips` | GPU · 반도체 |
| | | `pc-robotics` | AI PC & 로봇 |
| `ai-gaming` | **게임 테크** | `game-optimization` | 게임 최적화 · 엔진 |
| | | `ai-gameplay` | AI 게임 기술 |
| `guides` | **가이드** | `tutorials` | 실전 튜토리얼 |
| | | `compare` | 성능 비교 |

---

### 2. 생성 로직 연동 현황 (logic Alignment)
- **온라인 API 엔진 (`ai_news_editor.py`)**: 상기 8개 카테고리로 자동 분류 및 클러스터 매핑 로직 적용 완료.
- **로컬 Gemma4 엔진 (`stable_runner.py`)**: 단일 루프 기반 고품질 생성 안정화.
- **병렬 집필 엔진 (`local_parallel_writer.py`)**: 시스템 프리징 방지를 위해 2개 워커(max_workers=2)로 최적화 완료.
- **Hugo 연동 (`hugo.toml`)**: 대메뉴 UI 명칭 및 클러스터 슬러그 매칭 완료.
- **다국어 체계**: `content/en/...` 및 `content/ko/...` 경로에 90:90 대칭 저장 완료.

### 🎨 UI/UX 매핑 규칙
- **컬러 코딩**: AI(Blue #3B82F6), 하드웨어(Green #10B981), 게임테크(Purple #8B5CF6), 가이드(Orange #F59E0B)
- **태그 형식**: `[대분류 (중분류)]` 캡슐형 뱃지 (상단 좌측)
- **모바일 대응**: `white-space: nowrap` 적용 및 오버플로우 가로 스크롤 허용

---

## ✅ 프로젝트 마일스톤 (Checklist)

### **V0: 설계 및 구조 초기화**
- [x] 8개 핵심 슬러그 확정 및 디렉토리 생성
- [x] UI/UX 노출 규칙 및 컬러 매핑 정의
- [x] 레거시 데이터 아카이브 이동 (`backups/archive_vLegacy/`)
- [x] 신규 `hugo.toml` 대규모 업데이트 (메뉴/Taxonomy)

### **V1: 엔진 및 가이드 성능 고도화**
- [x] Gemma 4 로컬 모델 '8개 분류' 전용 프롬프트 고정
- [x] 뉴스 수집(Harvester) 키워드 8개 그룹 리밸런싱
- [ ] '실전 가이드' 자동 생성 트리거 로직 구현
- [x] 뉴스 카드 UI 템플릿 수정 (대/중분류 조합 노출)
- [x] 온라인 자동화 엔진에서 로컬 Gemma 4 제외 (순수 무료 API 체제 구축)
- [x] 다중 클라우드 폴백 시스템 구축 (OpenRouter, GitHub Models 연동)

### **V2: 안정화 및 상시 가동 시스템**
- [x] DB 경로 표준화 (절대 경로 도입) 및 파편화된 DB 병합 완료
- [x] NotebookLM MCP Integration (V2.1): 히스토리 DB 기반 소스 추출 기능 추가
- [/] 2시간 주기 뉴스 수집-분석-배포 파이프라인 상시 운영 (진행 중)
- [ ] 무료 API 쿼터 자동 모니터링 및 모델 스위칭 로직 강화
- [ ] 로컬 개발 환경(Qwen 2.5 14B)과 서버 배포 환경(Online APIs) 완전 분리 운영

---

## 📁 주요 디렉토리 맵
- `content/ko/clusters/`: 뉴스 기사 저장소
- `content/ko/guides/`: 튜토리얼 및 비교 리포트
- `automation/`: 자동화 스크립트 엔진
- `scratch/`: 임시 리포트 및 분석 데이터

---
**기록자**: Antigravity (AI Assistant)  
**동기화**: V2 파이프라인 고도화 진행 중. DB 표준화 완료.
