# 🚀 news.lego-sia.com 기술 스택 및 전문 역량 로드맵 (Skill Tree)

본 문서는 개발 PM의 관점에서 `news.lego-sia.com` 프로젝트의 성공적인 구축과 지속 가능한 운영을 위해 필요한 핵심 기술 역량과 관련 정보를 정리한 가이드입니다.

## 1. 핵심 기술 스택 (Core Skill Tree)

운영 효율성과 확장성을 극대화하기 위해 선정된 기술들을 4가지 주요 도메인으로 분류합니다.

### 1.1 Content & Framework (콘텐츠 엔진)
*   **Hugo (Go-based SSG)**: 정적 사이트 생성기 중 가장 빠른 빌드 성능 체득. Hugo 전용 템플릿 문법(Go Template) 이해 필수.
*   **Markdown Writing**: 단순 작성을 넘어, 체크리스트, 표, 코드 블록 등 확장 문법 활용 능력.
*   **Frontmatter Management**: YAML/TOML 형식을 통한 콘텐츠 메타데이터(카테고리, 태그, 시퀀스) 구조화 역량.

### 1.2 Design & Front-end (UI/UX 구현)
*   **Vanilla CSS (Modern)**: CSS Grid, Flexbox를 활용한 레이아웃 설계와 CSS Variables(Custom Properties)를 이용한 테마 시스템 구축.
*   **SCSS (Advanced)**: 대규모 스타일 파일 관리를 위한 Nesting, Mixins, 상속 개념 활용.
*   **A11Y (Web Accessibility)**: 시각 장애인 및 고령자를 고려한 명도 대비, 스크린 리더 친화적 마크업 설계.
*   **Modern JS (ES6+)**: 외부 라이브러리 없이 순수 JS로 다크모드 상호작용, 스크롤 하이라이트(TOC), 비동기 검색(Pagefind) 연동.

### 1.3 Infrastructure & DevOps (배포 및 자동화)
*   **Git / GitHub**: 브랜치 전략(Main/Feature)과 PR(Pull Request) 기반의 콘텐츠 검수 및 버전 관리.
*   **Netlify / Cloudflare Pages**: Edge Network 배포 최적화, 헤더 캐싱 설정, SSL 인증서 관리.
*   **GitHub Actions (CI/CD)**: 배포 전 이미지 최적화, 린팅(Linting), 사이트맵 제출 자동화 스크립트 구축.

### 1.4 Growth & SEO (마케팅 최적화)
*   **Technical SEO**: JSON-LD 구조화 데이터, Canonical 태그, Robots.txt/Sitemap.xml 제어.
*   **Google Analytics 4 (GA4)**: 사용자 유입 경로 분석 및 핵심 지표(스크롤 깊이, 클릭 이벤트) 트래킹 설정.
*   **Web Vitals**: LCP, FID, CLS 등 구글의 핵심 성능 지표 모니터링 및 성능 튜닝.

---

## 2. 도메인별 심화 학습 리스트 (Reference Info)

| 도메인 | 심화 항목 | 참고 키워드 |
| :--- | :--- | :--- |
| **Hugo Mastery** | Shortcodes 커스텀 제작 | 유튜브 임베드, 알림 박스, 이미지 캡션 자동화 |
| **UX/UI** | Glassmorphism 구현 | `backdrop-filter`, `opacity`, `blur` 최적화 |
| **Performance** | Image Processing | Hugo 내장 리사이징, WebP 변환, Lazy Loading |
| **Search** | Static Search Engine | Pagefind, Lunr.js, Algolia(SaaS) |

---

## 3. PM 권장 체크리스트 (운영 단계별)

### [Phase 1] 구축 단계
- [ ] Hugo 프로젝트 초기화 및 디렉토리 구조(archetypes 포함) 확립
- [ ] index.css 내에 컬러 팔레트 및 타이포그래피 변수 정의 여부
- [ ] 모바일 환경에서의 가독성(폰트 크기, 행간) 테스트 완료

### [Phase 2] 성장 단계
- [ ] 카테고리 확장(IT, Cooking)에 따른 전용 레이아웃 분리 적용
- [ ] 이미지 업로드 시 WebP 자동 변환 프로세스 동작 확인
- [ ] Google Search Console 등록 및 초기 색인 요청

### [Phase 3] 최적화 단계
- [ ] Lighthouse 성능 점수 90점 이상 유지 (Mobile/Desktop)
- [ ] 댓글 시스템(Giscus) 연동 및 실제 유저 피드백 수집 시작
- [ ] 외부 공유 시 한글 URL 인코딩 문제(og:url) 실기기 테스트

---

## 4. 전문가의 조언: 스킬트리 업데이트 방향

1.  **"Less is More"**: 정적 사이트의 본질은 가벼움입니다. 애니메이션이나 JS 라이브러리를 추가할 때는 항상 '성능 점수(Lighthouse)'를 먼저 확인하세요.
2.  **데이터 중심 사고**: 감에 의존한 카테고리 확장이 아닌, GA4 데이터를 통해 유입이 많은 키워드를 중심으로 IT나 요리 카테고리를 순차적으로 오픈하는 것을 추천합니다.
3.  **문서화의 습관**: 지금처럼 `docs/` 폴더를 활용해 의사결정 기록을 남기는 것은 훗날 협업 시 매우 강력한 레버리지가 됩니다.
