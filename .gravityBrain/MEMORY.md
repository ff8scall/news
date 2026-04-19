# 🧠 MEMORY: 뉴스 인텔리전스 시스템

## 📍 현재 상태
- **날짜**: 2026-04-20
- **단계**: NLM 프리미엄 파이프라인 중단 지점 복구 및 실행 중
- **최근 결정**: 
    - **중단 복구**: Antigravity 재시작 후 중단되었던 Hardware 섹션(ID 3~) 재개.
    - **버그 수정**: `notebooklm_publisher.py`에서 중복 기사 스킵 시 발생하는 `TypeError` 수정 완료.
    - **Throttling 강화**: 무료 티어 안전성을 위해 API 호출 간 20초 강제 대기 상시 적용.
    - **모델 최적화**: `gemini-3.1-flash-lite-preview`를 주력 엔진으로 확정.

## 🎯 단기 목표
- [x] 이미지 최적화 Tiered Strategy 구현 및 통합
- [x] 하이브리드 뉴스 파이프라인 (Legacy + Premium) 고도화 및 통합 완료
- [x] 국문 기사 헤더 통일 및 중복 제거 (상세 분석, 시사점)
- [x] API 기반 기사 3건 생성 테스트 (완료)
- [x] IndexNow 인증 최적화 (keyLocation 제거, User-Agent 강화) [v1.2]
- [x] NLM Premium 파이프라인 전체 공정 자동화 (수확->생성->배포->인덱싱) [v1.7]
- [x] 인증 만료 시 텔레그램 긴급 알림 및 상세 결과 보고서 연동
- [ ] 메가트렌드 분석 및 성능 비교 콘텐츠 보완 (Next)
- [ ] RSS 소스 추가 및 필터링 정교화 (Next)
- [ ] 실운영 자동화 스케줄링 검증 (Next)
