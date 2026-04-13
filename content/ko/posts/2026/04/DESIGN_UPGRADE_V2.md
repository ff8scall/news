# 🎨 Lego-sia 디자인 & UX 업그레이드 전략 문서 V2.0

본 문서는 뉴스의 '첫인상'을 결정짓는 UI/UX 개편 사항을 정의하며, 잊지 않도록 할 일 목록(To-Do)을 관리합니다.

---

## 🚀 1. 핵심 기능: 실시간 핫토픽 (Hot Topics)
*   **배치 위치**: 홈 메인 최상단 (Hero Section)
*   **표시 대상**: `news_main.py`에서 생성된 뉴스 중 AI 점수 **9점 이상**인 정예 기사 5건.
*   **디자인**: 
    - 가로로 흐르는 'Breaking News' 티커 바 (Ticker Bar) 적용.
    - 혹은 메인 최상단의 'Featured Article' 대형 카드 슬라이더 도입.

## 💎 2. 디자인 정밀 보정 (Premium UI)
*   **색상 체계 (Color Palette)**:
    - **Background**: Premium Deep Charcoal (#0B0E14)
    - **Accent**: Electric Blue (#00D2FF) & AI Violet (#702283) 그라데이션 적용.
*   **카드 디자인 (Glassmorphism)**: 
    - 카드 배경에 `backdrop-filter: blur(10px)`와 미세한 보더 라인 적용.
    - 그림자 효과(Box-shadow)를 다층적으로 쌓아 공중에 떠 있는 듯한 입체감 구현.
*   **타이포그래피**: 
    - 본문: 구글 폰트 'Pretendard' 혹은 'Inter' 적용 (가독성 극대화).
    - 제목: 'Outfit' 등 세리프가 없는 현대적 서체 활용.

## 📱 3. 사용자 경험 (UX) 최적화
*   **2-Depth 메뉴바**: 상단 네비게이션을 [Tech / Money / Hobby]로 1차 분류하고, 호버 시 세부 카테고리가 펼쳐지는 드롭다운 UI.
*   **무한 스크롤(Infinite Scroll)**: 독자가 카테고리 내부에서 끊김 없이 글을 읽을 수 있도록 비동기 로딩 구현 예정.
*   **이미지 에러 핸들링**: News API의 이미지가 깨질 경우를 대비한 **'Lego-sia 전용 플레이스홀더'** 디자인 적용 완료.

---

## 📝 4. 디자인 실천 항목 (To-Do List)
1.  [ ] `layouts/index.html`에 핫토픽 전용 히어로 섹션 마크업 추가.
2.  [ ] `assets/css/custom.css`에 글래스모피즘 카드 스타일 정의.
3.  [ ] 휴고의 `Params` 기능을 활용해 핫토픽 노출 여부 토글 버튼 생성.
4.  [ ] 모바일 햄버거 메뉴 레이아웃 재배치 (2단 계층 구조 반영).

---
*마지막 업데이트: 2026-04-10 (UI/UX Expert Antigravity)*
