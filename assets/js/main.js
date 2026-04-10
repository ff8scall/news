/* =================================================
   main.js - 핵심 인터랙션 (TOC 하이라이트, 헤더 스크롤, 다크모드, 모바일 메뉴)
   ================================================= */

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. 헤더 스크롤 감지 ─────────────────────
  const header = document.getElementById('site-header');
  if (header) {
    window.addEventListener('scroll', () => {
      header.classList.toggle('is-scrolled', window.scrollY > 10);
    }, { passive: true });
  }

  // ── 1.1 검색 모달 토글 ──────────────────────
  const btnSearch      = document.getElementById('btn-search');
  const btnSearchClose = document.getElementById('btn-search-close');
  const searchModal    = document.getElementById('search-modal');

  const toggleSearch = (state) => {
    if (searchModal) {
      searchModal.classList.toggle('is-open', state);
      searchModal.setAttribute('aria-hidden', String(!state));
      if (state) {
        setTimeout(() => {
          searchModal.querySelector('input')?.focus();
        }, 100);
      }
    }
  };

  if (btnSearch) btnSearch.addEventListener('click', () => toggleSearch(true));
  if (btnSearchClose) btnSearchClose.addEventListener('click', () => toggleSearch(false));
  searchModal?.querySelector('.search-modal-overlay')?.addEventListener('click', () => toggleSearch(false));

  // ESC 키로 닫기
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') toggleSearch(false);
  });

  // Pagefind UI 초기화
  if (window.PagefindUI) {
    new PagefindUI({
      element: "#search-ui",
      showSubResults: true,
      translations: {
        placeholder: "키워드를 입력하세요...",
        clear_search: "지우기",
        load_more: "더 보기",
        search_label: "이 사이트 검색",
        filters_label: "필터",
        zero_results: "[query]에 대한 검색 결과가 없습니다.",
        one_result: "[query]에 대해 1건의 결과가 있습니다.",
        many_results: "[query]에 대해 [count]건의 결과가 있습니다.",
        no_results: "결과를 찾을 수 없습니다."
      }
    });
  }

  // ── 2. 모바일 햄버거 메뉴 ────────────────────
  const btnHamburger = document.getElementById('btn-hamburger');
  const mobileNav    = document.getElementById('mobile-nav');
  if (btnHamburger && mobileNav) {
    btnHamburger.addEventListener('click', () => {
      const isOpen = mobileNav.classList.toggle('is-open');
      btnHamburger.classList.toggle('is-open', isOpen);
      btnHamburger.setAttribute('aria-expanded', String(isOpen));
      mobileNav.setAttribute('aria-hidden', String(!isOpen));
    });
  }

  // ── 3. 다크/라이트 모드 토글 ─────────────────
  const btnTheme  = document.getElementById('btn-theme');
  const iconMoon  = btnTheme?.querySelector('.icon-moon');
  const iconSun   = btnTheme?.querySelector('.icon-sun');
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (savedTheme === 'light' && iconMoon && iconSun) {
    iconMoon.style.display = 'none';
    iconSun.style.display  = 'block';
  }
  if (btnTheme) {
    btnTheme.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next    = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      if (iconMoon && iconSun) {
        iconMoon.style.display = next === 'dark' ? 'block' : 'none';
        iconSun.style.display  = next === 'light' ? 'block' : 'none';
      }
    });
  }

  // ── 4. TOC 스크롤 하이라이트 ─────────────────
  const tocLinks = document.querySelectorAll('#toc-nav a');
  if (tocLinks.length > 0) {
    const headings = Array.from(
      document.querySelectorAll('.post-content h2, .post-content h3')
    );
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute('id');
            tocLinks.forEach((link) => {
              link.classList.toggle(
                'is-active',
                link.getAttribute('href') === `#${id}`
              );
            });
          }
        });
      },
      { rootMargin: '-64px 0px -70% 0px' }
    );
    headings.forEach((h) => { if (h.id) observer.observe(h); });
  }

});
