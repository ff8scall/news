# 🛠️ Master Development Workflow & Task Tracker

본 문서는 `news.lego-sia.com` 프로젝트의 진행 상황을 한눈에 파악하고 진도를 체크하기 위한 마스터 작업표입니다.
각 단계별 작업이 완료될 때마다 체크(`[x]`) 표기하며 함께 확인하는 지표로 활용됩니다.

## Phase 1: 🏗️ 뼈대 구축 및 기본 셋팅 (Foundation)
- [x] **형상 관리 및 초기화 (버전 관리)**
  - `git init` 및 Hugo 전용 `.gitignore` 셋팅 (빌드 파일 제외)
- [x] **Hugo 환경 설정 및 디렉토리 고도화**
  - `hugo.toml` 언어, 사이트 설정, 네비게이션 메뉴 구조 정의
  - `layouts`, `assets`, `static` 기본 디렉토리 베이스 렌더링 확인
- [x] **디자인 시스템 (Design Tokens) 셋팅**
  - `assets/css/index.css` 초기화 및 프리텐다드(Pretendard) 폰트 연동
  - CSS Variables 기반 기초 테마 변수 (다크/라이트 코어 색상) 구축

## Phase 2: 🎨 UI/UX 및 코어 페이지 개발 (Frontend)
- [x] **공통 레이아웃(Layouts) 컴포넌트 개발**
  - `baseof.html` (전체 HTML 골격) 체계화
  - GNB 헤더 (Sticky & Glassmorphism) 및 하단 Footer 구조화
- [x] **사용자 경험(UX) 필수 페이지 및 기능 구현**
  - 메인 페이지 카드 리스트 노출 및 최적의 **Pagination(페이지네이션)** 연결
  - 상세 포스트 디자인 (TOC, 폰트 가독성 최적화)
  - 이탈 방지를 위한 **Custom 404 에러 페이지** 환경 구축
- [x] **디바이스 호환성 및 상호작용 플러그인 탑재**
  - **모바일 최우선(Mobile-first)** 반응형(Responsive) 작동 테스트 (미디어쿼리 완료)
  - 정적 검색 라이브러리(Pagefind) UI 추가 (검색 버튼 슬롯 확보 완료)

## Phase 3: 🔍 Advanced SEO 및 애드센스 시스템 (SEO & Ads)
- [x] **Advanced SEO 메타 태그 구현 (Tech SEO)**
  - `partials/seo.html` 분리: Title, Open Graph, Twitter Cards 동적 맵핑 매칭
  - **sitemap.xml 및 robots.txt** 커스텀 생성 및 노출 방어 셋팅
- [x] **퍼포먼스 방어 메커니즘 셋팅**
  - 이미지 용량 최소화를 위한 WebP 렌더링 스크립트 작성
  - 페이지 LCP 속도 방어를 위한 이미지 **Lazy Loading (`loading="lazy"`)** 일괄 적용 
- [x] **데이터 트래킹 및 구조화 스키마**
  - Article, Breadcrumbs 등 카테고리 기반 구글 리치 스키마(JSON-LD) 생성
  - **GA4 (애널리틱스) 및 GSC (서치콘솔)** 코드 삽입부 셋팅
- [x] **애드센스(AdSense) 수익화 공간 디자인**
  - 리스트 뷰어 사이, 본문 영역 최적화된 광고 랜딩 슬롯 셋팅 및 자동 광고 반응형 처리

## Phase 4: 🤖 인공지능 콘텐츠 테스트 및 최종 점검 (Test & Launch)
- [x] **더미(Dummy) 트렌드 콘텐츠 발행 테스트**
  - 설계된 캠핑/테크 트렌드 기반 샘플 포스트 3종 작성 (완료)
  - 카테고리/태그 연동 상태 검증 (완료)
- [x] **최종 배포 아키텍처 자동화 (CI/CD)**
  - GitHub 푸시 이벤트 기반의 **Netlify 배포 자동화** 스크립트 완성 (`netlify.toml` 구성 완료)
  - Hugo 빌드 성공 점검 ✅ (78ms 빌드, 0 에러)
- [x] **최종 성능 및 배포 점검 (Lighthouse 90+)**
  - 페이지 로드, 모바일 접근성, SEO 스코어 정위치 점검
  - Hugo 서버 로컬 실행 및 41페이지 정상 빌드 확인 ✅

## Phase 5: 🤖 콘텐츠 수집 및 생산 자동화 (AI Automation)
- [ ] **실시간 트렌드 수집 엔진 구축**
  - Google Trends / SNS 기반 핫 키워드 추출 로직 설계
- [ ] **AI 콘텐츠 제너레이터 (Writer) 연동**
  - GPT-4 / Gemini API 기반 SEO 최적화 포스팅 생성 자동화
- [ ] **자동화 파이프라인 (GitHub Actions) 셋팅**
  - 매일 특정 시간에 자동으로 수집 -> 작성 -> Push -> 배포되는 풀(Full) 자동화 완성

---

> 💡 **사용 방법 (How to track):**
> 실제 개발을 진행하면서 특정 단위 작업이 끝날 때마다 제가 이 파일로 돌아와 진행된 부분에 `[x]` 표시를 남기겠습니다. 이 문서를 통해 언제든 전체 공정률을 한눈에 파악하실 수 있습니다!
