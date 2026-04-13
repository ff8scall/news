# 🔍 news.lego-sia.com 검색 유입 극대화 SEO 전략 보고서

본 문서는 `news.lego-sia.com`의 검색 엔진 노출(SEO)을 최적화하여 오가닉 유입을 극대화하기 위한 전문가용 가이드입니다. 

## 1. 도메인 및 URL 아키텍처 (Technical SEO)

### 1.1 서브도메인 브랜드 강화
*   **도메인**: `news.lego-sia.com` 
*   **전략**: 메인 서비스(`lego-sia.com`)의 브랜드 지수를 공유하면서 뉴스 전문성을 강조하기 위해 서브도메인을 유지합니다. 전 구간 **HTTPS** 적용은 필수입니다.

### 1.2 URL 가독성 및 계층 구조
*   **한글 URL 전략**: `/:section/:slug/` (예: `/camping/초보-캠핑장-예약-팁/`)
    *   **장점**: 국내 환경에서 클릭률(CTR)이 높고 직관적임.
    *   **주의**: SNS 공유 시 인코딩 문제를 방지하기 위해 Hugo 설정에서 `removePathAccents = false`와 더불어 필요시 Frontmatter에서 수동으로 깔끔한 슬러그(`slug`)를 지정하는 습관이 중요합니다.
*   **Trailing Slash**: URL 끝에 `/`를 일관되게 붙여 중복 콘텐츠 이슈를 방지합니다.

## 2. 온페이지 SEO 핵심 체크리스트 (On-Page SEO)

### 2.1 마크업 구조화 (Heading Hierarchy)
*   `<h1>`: 페이지당 반드시 1개 사용 (포스트 제목).
*   `<h2>`, `<h3>`: 목차(TOC)와 연동되는 소주제 제목. 키워드를 자연스럽게 포함해야 함.
*   **Alt Text**: 모든 이미지에 `alt` 속성을 부여하여 이미지 검색 유입을 확보합니다.

### 2.2 메타 태그 최적화
*   **Title Tag**: `[포스트 제목] | news.lego-sia.com` 또는 `[포스트 제목] - 캠핑과 라이프스타일` (60자 이내).
*   **Meta Description**: 핵심 키워드를 포함한 본문 요약 (150자 이내). 검색 결과 상 노출되는 문구이므로 클릭 유도(CTA) 표현 포함.
*   **Open Graph & Twitter Cards**: 페이스북, 카카오톡 등에 공유될 때 노출되는 썸네일과 제목 설정.

### 2.3 구조화 데이터 (JSON-LD)
*   **Article 스키마**: 구글 검색 결과에서 뉴스나 포스트 형태로 리치하게 노출.
*   **Breadcrumb 스키마**: 검색 결과 하단에 계층형 경로 표시 유도.
*   **FAQ 스키마**: 질문/답변 형식의 콘텐츠 작성 시 검색 결과 면적을 크게 차지하여 CTR 상승.

## 3. 기술적 최적화 및 관리 (Advanced SEO)

### 3.1 내부 링크 및 사이트맵
*   **Internal Linking**: 본문 내에 관련 있는 이전 포스트 링크를 자연스럽게 삽입하여 체류 시간(Dwell Time)을 늘리고 크롤러의 탐색을 돕습니다.
*   **XML Sitemap & Robots.txt**: Hugo에서 자동으로 생성되는 `sitemap.xml`을 검색 엔진에 등록합니다. `robots.txt`를 통해 불필요한 경로(예: `/tags/`, `/categories/`의 페이지네이션 등) 크롤링 낭비를 방지합니다.

### 3.2 성능 및 코어 웹 바이탈 (Performance)
*   **LCP (Largest Contentful Paint)**: 대표 이미지 WebP 사용 및 우선 로딩으로 1.5초 이내 달성.
*   **CLS (Cumulative Layout Shift)**: 레이아웃 흔들림 방지. 이미지 크기(width, height) 명시.
*   **모바일 친화성**: Netlify 배포 후 구글 모바일 친화성 테스트 통과 필수.

## 4. 콘텐츠 전략 (Content SEO)

### 4.1 E-E-A-T 강화
*   **Experience, Expertise, Authoritativeness, Trustworthiness**: 캠핑 장비 리뷰나 요리 팁 작성 시 본인의 실제 경험임을 증명하는 사진과 전문적인 의견을 포함하여 구글의 신뢰를 확보합니다.
*   **Author Profile**: 포스트 하단에 저자 정보를 표시하여 콘텐츠의 신뢰도를 높입니다.

### 4.2 주제 클러스터링 (Topic Clusters)
*   **필라 페이지**: '캠핑 초보 가이드'와 같은 거대 주제를 다루는 포스트.
*   **클러스터 콘텐츠**: '캠핑장 예약 방법', '필수 캠핑 용품' 등 세부 주제 포스트들.
*   이들을 서로 정교하게 연결하여 해당 주제의 권위자로 인식되게 합니다.

---

## 5. 포스트 런칭 후 액션 아이템 (Post-Launch)

1.  **Google Search Console**: 배포 즉시 사이트맵 등록 및 수동 색인 요청.
2.  **Naver Search Advisor & Bing Webmaster Tools**: 국내/글로벌 검색 유입을 위해 추가 등록.
3.  **GA4 모니터링**: 어떤 키워드로 유입되는지 확인하여 인기 있는 주제의 연관 포스트를 추가 작성.
4.  **IndexNow 적용**: (Hugo & Netlify 환경) 콘텐츠 수정 시 즉시 검색엔진에 알림을 보내는 IndexNow 라이브러리 연동 고려.
