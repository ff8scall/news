# 🧠 PROJECT BRAIN: 레고-시아 V0 (Genesis)

> **현재 시점**: 2026-04-13  
> **상태**: 신규 설계 시스템 초기화 및 동기화 중  
> **슬로건**: "AI와 게임, 오직 트래픽과 가치에 집중한다."

## 🏛️ V0 확정 시스템 설계 (System Blueprint)

### 1. 4대 코어 카테고리 (Taxonomy)
| 클러스터 (대분류) | 슬러그 | 세부 분류 (중분류) | 슬러그 | UI 태그 노출 예시 |
| :--- | :--- | :--- | :--- | :--- |
| **AI 모델 & 도구** | `ai-models-tools` | AI 모델·트렌드 | `ai-models` | **AI (AI 모델·트렌드)** |
| | | AI 도구·사용법 | `ai-tools` | **AI (AI 도구·사용법)** |
| **GPU & 하드웨어** | `gpu-hardware` | GPU·반도체 | `gpu-chips` | **하드웨어 (GPU·반도체)** |
| | | AI PC & 로봇 | `pc-robotics` | **하드웨어 (AI PC & 로봇)** |
| **게임 최적화 & 테크** | `ai-gaming` | 게임 최적화·엔진 | `game-optimization` | **게임 테크 (최적화·엔진)** |
| | | AI 게임 기술 | `ai-gameplay` | **게임 테크 (AI 게임 기술)** |
| **전략 가이드** | `guides` | 실전 튜토리얼 | `tutorials` | **가이드 (실전 튜토리얼)** |
| | | 성능 비교 | `compare` | **가이드 (성능 비교)** |

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

---

## 📁 주요 디렉토리 맵
- `content/ko/clusters/`: 뉴스 기사 저장소
- `content/ko/guides/`: 튜토리얼 및 비교 리포트
- `backups/archive_vLegacy/`: 구 버전 유산 보관함

---
**기록자**: Antigravity (AI Assistant)  
**동기화**: V0 초기화 완료. 다음 단계(`hugo.toml`) 대기 중.
