import os
import json
import time
import re
import logging
import argparse
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
        print(f"DEBUG: news_main file path: {nm.__file__}", flush=True)
        jobs = self.load_jobs()
        if not jobs:
            logger.info("No pending premium jobs found.")
            return

        published_count = 0
        all_published_urls = []
        
        # [V1.6] 결과 요약 객체
        summary = {"published": 0, "indexed": 0, "urls": []}
        
        for cat, job in jobs.items():
            if job.get("status") == "published":
                continue

            nb_id = job["notebook_id"]
            mode = job.get("mode", "A")
            
            logger.info(f"Checking status for {cat} (Mode {mode}, {nb_id})...")
            
            # [V4.5] 리포트 완료 대기 로직 (최대 5분)
            report = None
            for attempt in range(30): # 10초 * 30 = 300초(5분)
                report = self.app.get_latest_report(nb_id)
                if report and report.get("status") == "completed":
                    break
                
                status_str = report.get("status", "unknown") if report else "not_found"
                logger.info(f"  ...Report {status_str}. Waiting 10s (Attempt {attempt+1}/30)...")
                time.sleep(10)
            
            if not report or report.get("status") != "completed":
                logger.warning(f" [SKIP] Report timed out or not ready for {cat}")
                continue
                
            report_id = report["id"]
            logger.info(f" [DONE] Report found ({report_id}) for {cat}. Downloading...")
            
            # 2. 리포트 본문 다운로드
            content = self.app.download_report(nb_id, report_id)
            if not content:
                logger.error(f"Failed to download report for {cat}")
                continue

            # 로컬 저장 (디버깅용)
            report_path = os.path.join(self.output_dir, f"{cat}_report.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 3. 파싱 및 게시
            success = False
            if mode == "A":
                success = self._publish_mode_a(content, cat, job)
            elif mode == "B":
                success = self._publish_mode_b(content, cat, job)
            
            if success:
                job["status"] = "published"
                job["published_at"] = datetime.now().isoformat()
                published_count += 1
                
                # [V1.5] URL 수집 (IndexNow용)
                if "urls" in job:
                    all_published_urls.extend(job["urls"])
        
        if published_count > 0:
            self.save_jobs(jobs)
            logger.info(f"Batch publishing completed. Total {published_count} jobs updated.")
            
        summary["published"] = published_count
        summary["urls"] = all_published_urls
        return summary



    def _pre_generate_image(self, article, slug):
        """[V10.0] Tiered Image Strategy: 원본/라이브러리/생성 계층적 처리"""
        from image_manager import get_tiered_image
        return get_tiered_image(article, slug)

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
        article["thumbnail_image"] = img_url
        
        # 한국어 포스트 생성
        nm.create_hugo_post(article, lang='ko')
        logger.info(f" [KO] Megatrend editorial saved for {category}")
        
        # 영문 번역 생성
        eng_article = self._generate_english_from_korean(article)
        if eng_article:
            eng_article["_shared_image"] = img_url
            nm.create_hugo_post(eng_article, lang='en')
            logger.info(f" [EN] English version saved for {category}")
        
        # [V1.5] URL 기록
        date_path = datetime.now().strftime("%Y/%m/%d")
        job_info["urls"] = [
            f"https://news.lego-sia.com/posts/{date_path}/{article['sync_slug']}/",
            f"https://news.lego-sia.com/en/posts/{date_path}/{article['sync_slug']}/"
        ]
        
        return True


    def _publish_mode_b(self, content, category, job_info):
        """모드 B: 구조화 데이터 기반 다건 기사 발행"""
        articles = parse_structured_articles(content)
        if not articles:
            logger.warning(f"Mode B: No valid articles parsed for {category}")
            return False
            
        logger.info(f"Successfully parsed {len(articles)} articles.")
        
        # 순차 처리 (병렬화 가능하지만 안정성 우선)
        job_info["urls"] = []
        for article in articles:
            url_ko, url_en = self._publish_single_article(article)
            if url_ko: job_info["urls"].append(url_ko)
            if url_en: job_info["urls"].append(url_en)
            
        logger.info(f"Mode B: Published {len(articles)} articles for {category}")
        return True

    def _publish_single_article(self, article):
        """[Helper] 단일 기사 처리 (병렬용)"""
        # [V4.8] 슬러그 정규화: {cluster}-{slug} 형식 강제 및 50자 제한
        raw_title = article.get("eng_title") or article.get("kor_title") or f"Article {article.get('id', 'Unknown')}"
        cluster = article.get("cluster", "tech")
        raw_slug = nm.sanitize_slug(raw_title)
        
        if raw_slug and not raw_slug.isdigit():
            # 대분류 접두사 추가 및 전체 50자 제한
            slug = f"{cluster}-{raw_slug}"[:50].strip('-')
        else:
            # 제목이 부실한 경우: {cluster}-{category}-{id}
            article_id = str(article.get("id", "0")).zfill(2)
            category = article.get("category", "news")
            slug = f"{cluster}-{category}-{article_id}"
        
        article["sync_slug"] = slug
        article["original_url"] = article.get("original_url", "")
        article["original_image_url"] = article.get("original_image")
        article["source_name"] = "NotebookLM Premium"
        
        # [V4.4] 중복 발행 건너뛰기 로직
        if nm.is_already_published(slug):
            logger.info(f"  [SKIP] Article already exists: {slug}")
            return None, None
        
        # 이미지 1회 생성 후 한/영 공유
        img_url = self._pre_generate_image(article, slug)
        article["thumbnail_image"] = img_url
        
        try:
            nm.create_hugo_post(article, lang='ko')
            nm.create_hugo_post(article, lang='en')
            
            # URL 생성 규칙 (news_main과 동일)
            date_path = datetime.now().strftime("%Y/%m/%d")
            url_ko = f"https://news.lego-sia.com/posts/{date_path}/{slug}/"
            url_en = f"https://news.lego-sia.com/en/posts/{date_path}/{slug}/"
            return url_ko, url_en
        except Exception as e:
            logger.error(f"Failed to create Hugo post for {slug}: {e}")
            return None, None

    def _generate_english_from_korean(self, article):
        """[Draft] 한국어 기사를 바탕으로 영문 버전 생성 (Gemini 활용 가능)"""
        # 현재는 NLM이 영문/국문을 모두 준다고 가정하거나, 간단히 필드 교체
        eng = article.copy()
        if "eng_title" in article: eng["title"] = article["eng_title"]
        if "eng_content" in article: eng["content"] = article["eng_content"]
        if "eng_summary" in article: eng["summary"] = article["eng_summary"]
        if "thumbnail_image" in article: eng["thumbnail_image"] = article["thumbnail_image"]
        return eng


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", help="Specific category to process")
    parser.add_argument("--skip-ai-img", action="store_true", help="Skip AI image generation")
    args = parser.parse_args()

    if args.skip_ai_img:
        os.environ["SKIP_AI_IMAGE"] = "1"

    pub = NotebookLMPublisher()
    pub.process_pending_jobs()
