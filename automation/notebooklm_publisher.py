import os
import json
import time
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from notebooklm_prep import NotebookLMApp
from nlm_parser import parse_structured_articles, parse_editorial_markdown
from common_utils import send_telegram_report
from ai_writer import AIWriter

# news_main의 Hugo 포스트 생성 함수 재사용
import news_main as nm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NotebookLM_Publisher")


class NotebookLMPublisher:
    """
    NotebookLM Premium Pipeline - Phase 2: 다운로드 → 파싱 → Hugo 게시
    
    모드 A: 마크다운 사설 → parse_editorial_markdown → create_hugo_post
    모드 B: 구조화 데이터 → parse_structured_articles → create_hugo_post (다건)
    모드 C: 영문 구조화 데이터 → parse → 로컬 모델 한국어화 → create_hugo_post
    """
    def __init__(self):
        self.app = NotebookLMApp()
        self.writer = AIWriter()
        self.jobs_file = "automation/premium_jobs.json"
        self.output_dir = "scratch/premium_reports"
        os.makedirs(self.output_dir, exist_ok=True)

    def load_jobs(self):
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_jobs(self, jobs):
        with open(self.jobs_file, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=4, ensure_ascii=False)

    def process_pending_jobs(self):
        """모든 대기 중인 Job을 확인하고 완료된 것을 게시"""
        jobs = self.load_jobs()
        if not jobs:
            logger.info("No pending premium jobs found.")
            return

        published_count = 0
        for cat, job in jobs.items():
            if job.get("status") == "published":
                continue

            nb_id = job["notebook_id"]
            mode = job.get("mode", "A")
            logger.info(f"Checking status for {cat} (Mode {mode}, {nb_id})...")
            
            # NLM 아티팩트 상태 확인
            status_res = self.app.check_status(nb_id)
            if not status_res or not isinstance(status_res, list):
                logger.warning(f"Cannot check status for {cat}. Skipping.")
                continue

            # 완료된 리포트 찾기
            reports = [a for a in status_res if a.get("type") == "report" and a.get("status") == "completed"]
            
            if not reports:
                logger.warning(f"No completed report for {cat} yet. Will retry later.")
                continue

            # 가장 최근 리포트 다운로드
            report_artifact = reports[-1]
            logger.info(f" [DONE] Report found ({report_artifact['id']}) for {cat}. Downloading...")
            
            filepath = os.path.join(self.output_dir, f"{cat}_report.md")
            abs_filepath = os.path.abspath(filepath)
            
            self.app.run_cmd(["download", "report", nb_id, "--output", abs_filepath], use_json=False)
            
            if not os.path.exists(abs_filepath):
                logger.error(f"Failed to download report for {cat}")
                continue

            # 모드별 처리 분기
            with open(abs_filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()

            if mode == "A":
                success = self._publish_mode_a(raw_content, cat, job)
            elif mode == "B":
                success = self._publish_mode_b(raw_content, cat, job)
            elif mode == "C":
                success = self._publish_mode_c(raw_content, cat, job)
            else:
                success = self._publish_mode_a(raw_content, cat, job)

            if success:
                job["status"] = "published"
                job["published_at"] = datetime.now().isoformat()
                published_count += 1
                logger.info(f" [SUCCESS] Category '{cat}' published (Mode {mode}).")

        self.save_jobs(jobs)
        
        if published_count > 0:
            msg = f"🚀 [Premium Pipeline] {published_count} editorial(s) published!"
            try:
                send_telegram_report(msg)
            except:
                pass

    # ===================================================================
    # 모드별 게시 로직
    # ===================================================================
    
    def _pre_generate_image(self, article, slug):
        """[V2.1] 기사당 이미지 1회 생성 후 한/영 공유"""
        img_url = nm.generate_and_save_thumbnail(article.get('image_prompt_core'), slug)
        if img_url:
            logger.info(f" [IMAGE] AI Generated for {slug}")
        else:
            cat = nm.sanitize_slug(article.get('category', 'ai-models'))
            fallback_key = nm.FALLBACK_MAP.get(cat, 'ai-tech')
            img_url = f"/images/fallbacks/{fallback_key}.jpg"
            logger.info(f" [IMAGE] Using fallback for {slug}")
        return img_url

    def _publish_mode_a(self, raw_content, category, job_info):
        """모드 A: 마크다운 사설 → 단일 프리미엄 기사"""
        article = parse_editorial_markdown(raw_content, category=category)
        if not article:
            logger.error(f"Mode A: Failed to parse editorial for {category}")
            return False

        date_slug = datetime.now().strftime("%Y-%m-%d")
        article["sync_slug"] = f"megatrend-{category}-{date_slug}"
        article["original_url"] = ""
        article["original_image_url"] = None
        article["source_name"] = "NotebookLM Premium"
        
        # 이미지 1회 생성 후 한/영 공유
        img_url = self._pre_generate_image(article, article["sync_slug"])
        article["_shared_image"] = img_url
        
        # 한국어 포스트 생성
        nm.create_hugo_post(article, lang='ko')
        logger.info(f" [KO] Megatrend editorial saved for {category}")
        
        # 영문 번역 생성
        eng_article = self._generate_english_from_korean(article)
        if eng_article:
            eng_article["_shared_image"] = img_url
            nm.create_hugo_post(eng_article, lang='en')
            logger.info(f" [EN] English version saved for {category}")
        
        return True

    def _publish_single_article(self, article):
        """[Helper] 단일 기사 처리 (병렬용)"""
        slug = nm.sanitize_slug(article.get("eng_title", f"article-{article.get('id', 0)}"))
        article["sync_slug"] = slug
        article["original_url"] = ""
        article["original_image_url"] = None
        article["source_name"] = "NotebookLM Premium"
        
        # 이미지 1회 생성 후 한/영 공유
        img_url = self._pre_generate_image(article, slug)
        article["_shared_image"] = img_url
        
        try:
            nm.create_hugo_post(article, lang='ko')
            nm.create_hugo_post(article, lang='en')
            logger.info(f" [OK] Published: {article.get('eng_title', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f" [FAIL] {slug}: {e}")
            return False

    def _publish_mode_b(self, raw_content, category, job_info, test_limit=None):
        """모드 B: 구조화 데이터 → 다수 개별 기사 (병렬 처리 지원)"""
        articles = parse_structured_articles(raw_content)
        if not articles:
            logger.error(f"Mode B: No articles parsed for {category}")
            return False

        if test_limit:
            logger.info(f"Mode B: TEST MODE - Limiting to first {test_limit} articles.")
            articles = articles[:test_limit]

        logger.info(f"Mode B: Starting stable parallel publication with 3 workers for {len(articles)} articles...")
        
        # [V2.2] ThreadPoolExecutor를 사용한 안정적인 병렬 처리 (최대 3개 동시 작업)
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(self._publish_single_article, articles))

        success_count = sum(1 for r in results if r)
        logger.info(f"Mode B: Published {success_count}/{len(articles)} articles for {category}")
        return success_count > 0

    def _publish_mode_c(self, raw_content, category, job_info):
        """모드 C: 영문 구조화 데이터 → 로컬 모델로 한국어화"""
        articles = parse_structured_articles(raw_content)
        if not articles:
            logger.error(f"Mode C: No articles parsed for {category}")
            return False

        success_count = 0
        for article in articles:
            slug = nm.sanitize_slug(article.get("eng_title", f"article-{article.get('id', 0)}"))
            article["sync_slug"] = slug
            article["original_url"] = ""
            article["original_image_url"] = None
            article["source_name"] = "NotebookLM Premium"
            
            # 한국어 필드가 비어있으면 로컬 모델로 생성
            if not article.get("kor_title") or not article.get("kor_content"):
                logger.info(f" [GEN] Localizing to Korean via local model: {slug}")
                kor_data = self._localize_to_korean(article)
                if kor_data:
                    article.update(kor_data)
                else:
                    logger.warning(f" [SKIP] Korean localization failed for {slug}")
                    continue
            
            try:
                nm.create_hugo_post(article, lang='ko')
                nm.create_hugo_post(article, lang='en')
                success_count += 1
            except Exception as e:
                logger.error(f" [FAIL] {slug}: {e}")

        logger.info(f"Mode C: Published {success_count}/{len(articles)} articles for {category}")
        return success_count > 0

    # ===================================================================
    # 번역/현지화 헬퍼
    # ===================================================================

    def _generate_english_from_korean(self, kor_article):
        """한국어 기사 → 영문 기사 데이터 생성 (모드 A용)"""
        prompt = (
            f"Translate and adapt this Korean tech editorial into a professional English article.\n"
            f"Output ONLY the article body in markdown format. No frontmatter.\n"
            f"Tone: TechCrunch/Wired senior editor.\n\n"
            f"Korean Title: {kor_article.get('kor_title')}\n"
            f"Korean Content:\n{kor_article.get('kor_content', '')[:3000]}"
        )
        
        eng_content = self.writer.generate_content(prompt, role="writing")
        if not eng_content or len(eng_content) < 200:
            return None

        # 영문 제목 추출 시도 (첫 줄이 # 으로 시작하면)
        lines = eng_content.strip().split("\n")
        eng_title = kor_article.get("kor_title", "Megatrend Analysis")
        for line in lines:
            if line.startswith("#"):
                eng_title = re.sub(r'^#+\s*', '', line).strip()
                break
        
        return {
            **kor_article,
            "eng_title": eng_title,
            "eng_description": eng_title,
            "eng_summary": eng_title,
            "eng_keywords": kor_article.get("kor_keywords", []),
            "eng_content": eng_content,
        }

    def _localize_to_korean(self, eng_article):
        """영문 기사 → 한국어 현지화 (모드 C용, 로컬 모델 사용)"""
        prompt = (
            f"다음 영문 테크 기사를 전문 저널리즘 수준의 한국어 기사로 변환하라.\n"
            f"개조식 금지. 서술형 문단 구성. AI 필러 문구 금지.\n\n"
            f"English Title: {eng_article.get('eng_title')}\n"
            f"English Content:\n{eng_article.get('eng_content', '')[:3000]}\n\n"
            f"출력 형식 (JSON):\n"
            f'{{"kor_title": "...", "kor_content": "...", "kor_summary": ["...", "..."], '
            f'"kor_insight": "...", "kor_keywords": ["...", "..."]}}'
        )
        
        # 로컬 모델 사용 (qwen2.5-coder:14b)
        result = self.writer.generate_content(prompt, model="qwen2.5-coder:14b")
        if not result:
            return None

        # JSON 추출
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(), strict=False)
            except:
                pass
        
        return None


if __name__ == "__main__":
    publisher = NotebookLMPublisher()
    publisher.process_pending_jobs()
