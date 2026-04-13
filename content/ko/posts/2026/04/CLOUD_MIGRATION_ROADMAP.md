# 🚀 클라우드 마이그레이션 전략 로드맵 (Cloud Roadmap)

## 1. 비전
로컬 환경의 기술적 가변성을 제거하고, GitHub Actions 기반의 24/7 무인 배포 체계를 구축하여 운영 효율성을 극대화한다.

## 2. 마이그레이션 단계 (4-Phase Strategy)

### 🟢 Phase 1: 로컬 안정화 및 지능 고도화 (현재)
- **중점**: AI 편집국(기자+국장)의 협업 품질 검증.
- **작업**:
    - AI 국장의 Reject 사유 분석 및 프롬프트 미세 조정.
    - 이미지 폴백 시스템의 완벽한 작동 확인.
    - 텔레그램 리포트의 가독성 향상.
- **기간**: 약 3~7일간의 무결점 가동 확인.

### 🟡 Phase 2: 클라우드 이식 준비 (Standardization)
- **중점**: "어디서나 돌아가는 코드"로 체질 개선.
- **작업**:
    - `requirements.txt` 최신화.
    - API 키 보안 (GihHub Secrets 연동 설계).
    - 리눅스 서버(Ubuntu) 환경 호환성 테스트.

### 🟠 Phase 3: GitHub Actions 파일럿 (Pilot)
- **중점**: 2시간 주기(Cron) 스케줄러 최초 가동.
- **작업**:
    - `.github/workflows/daily_news.yml` 구축.
    - 초기 수동 실행을 통한 'IndexNow' 및 'Telegram' 연동 성공 확인.

### 🔴 Phase 4: 완전 무인 운영 (Production)
- **중점**: 로컬 PC 독립 및 클라우드 네이티브 운영.
- **작업**:
    - 2시간 주기의 정기 배포 안정화.
    - 원격 제어(Telegram Bot Command) 기능 강화.

## 3. 리스크 관리
- **Actions 사용량**: 2시간 주기로 설정하여 무료 한도(2,000분) 내에서 안정적으로 운영.
- **보안**: 모든 API 키는 GitHub Secrets에만 저장하여 코드 유출 방지.

---
*Created by Antigravity AI Strategist on 2026-04-11*
