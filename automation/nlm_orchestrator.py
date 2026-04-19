# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import argparse
import subprocess
import traceback
from datetime import datetime

# 현재 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from notebooklm_prep import process_macro_synthesis, NotebookLMApp
from notebooklm_publisher import NotebookLMPublisher
from common_utils import send_telegram_report
from indexnow_service import notify_indexnow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("automation/nlm_orchestrator.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LegoSia.NLM_Orchestrator")


def git_sync():
    """변경된 기사 파일을 GitHub에 커밋하고 푸시하여 배포 트리거"""
    logger.info(" [GIT] Syncing changes to GitHub...")
    try:
        # 1. Add
        subprocess.run(["git", "add", "."], check=True)
        # 2. Commit
        commit_msg = f"chore: premium news update {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=False) # 변경사항 없을 수 있음
        # 3. Pull (Rebase)
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
        # 4. Push
        subprocess.run(["git", "push"], check=True)
        logger.info(" [GIT] Successfully pushed to GitHub.")
        return True
    except Exception as e:
        logger.error(f" [GIT] Sync failed: {e}")
        return False


def run_phase1(mode="A", limit=15, source="rss"):
    """Phase 1: 뉴스 데이터 준비 → NotebookLM 리포트 트리거"""
    logger.info("=" * 60)
    logger.info(f" [PHASE 1] Preparing Data (Mode {mode}, Limit {limit})...")
    
    # 1. 인증 체크
    app = NotebookLMApp()
    if not app.verify_auth():
        logger.error(" [AUTH] NotebookLM session expired. Please run 'nlm login' manually.")
        return None
        
    # 2. 파이프라인 실행
    jobs = process_macro_synthesis(limit_per_cat=limit, mode=mode, source=source)
    if not jobs:
        logger.error(" [PHASE 1 FAIL] No articles were processed.")
        return None
        
    logger.info(f" [PHASE 1 OK] Triggered {len(jobs)} reports in NotebookLM.")
    return jobs


def run_phase2():
    """Phase 2: 상태 확인 및 결과물 게시 (수동 호출용)"""
    logger.info("=" * 60)
    logger.info(" [PHASE 2] Checking Status & Publishing...")
    
    t0 = time.time()
    publisher = NotebookLMPublisher()
    summary = publisher.process_pending_jobs()
    t1 = time.time()
    
    logger.info(f"[PHASE 2 OK] Completed in {t1-t0:.1f}s.")
    return summary


def run_full_pipeline(mode="A", limit=15, source="rss", poll_interval=60, max_wait=900):
    """
    [V2.0] Full Automated Pipeline with Stage-wise Telegram Notifications
    """
    try:
        # [START NOTIFICATION]
        send_telegram_report(f"🚀 <b>[Premium Pipeline]</b> Start\nMode: {mode} | Source: {source} | Limit: {limit}")
        
        start_time_total = time.time()
        total_published = 0
        total_indexed = 0
        
        # Phase 1: 데이터 수집 및 NLM 전송
        active_jobs = run_phase1(mode=mode, limit=limit, source=source)
        if not active_jobs:
            logger.error("Pipeline aborted: Phase 1 failed.")
            return

        # [STEP 1&2 NOTIFICATION]
        job_count = len(active_jobs)
        send_telegram_report(
            f"📥 <b>[Step 1&2] Done</b>\n"
            f"• RSS Harvested & Filtered\n"
            f"• {job_count} Notebooks created\n"
            f"• NLM Reports triggered. Polling status..."
        )
        
        # Phase 2: 폴링 및 배포
        logger.info(f" [PHASE 2] Starting polling every {poll_interval}s (Max {max_wait}s)...")
        publisher = NotebookLMPublisher()
        waited = 0
        
        while waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            logger.info(f" [POLL] {waited}s elapsed. Checking status...")
            
            # 일부만 완료된 경우에도 게시 시도
            summary = publisher.process_pending_jobs()
            if summary:
                new_p = summary.get("published", 0)
                if new_p > 0:
                    total_published += new_p
                    # 배포 및 인덱싱
                    if git_sync():
                        urls = summary.get("urls", [])
                        if urls:
                            logger.info(f" [IndexNow] Notifying for {len(urls)} URLs...")
                            notify_indexnow(urls)
                            total_indexed += len(urls)
            
            # 모든 Job이 published 상태인지 확인
            try:
                with open("automation/premium_jobs.json", "r", encoding="utf-8") as f:
                    jobs_data = json.load(f)
                    all_done = all(j.get("status") == "published" for j in jobs_data.values())
                    if all_done:
                        logger.info("[DONE] All jobs published successfully!")
                        break
            except Exception as e:
                logger.debug(f"Error checking jobs status: {e}")
        
        if waited >= max_wait:
            logger.warning(f"[TIMEOUT] Max wait ({max_wait}s) reached.")

        logger.info("\n[PIPELINE COMPLETE]")
        
        # [FINISH NOTIFICATION]
        report_msg = (
            f"✅ <b>[Premium Pipeline]</b> Finished!\n\n"
            f"• Mode: {mode}\n"
            f"• Published: {total_published} articles\n"
            f"• Indexed: {total_indexed} URLs\n"
            f"• Time Taken: {int((time.time() - start_time_total)/60)}m"
        )
        send_telegram_report(report_msg)

    except Exception as e:
        err_trace = traceback.format_exc()
        logger.error(f" [CRITICAL ERROR] Pipeline crashed: {e}\n{err_trace}")
        
        # [ERROR NOTIFICATION]
        error_msg = f"❌ <b>[Premium Pipeline] CRASHED</b>\n\n<b>Error:</b> {str(e)}\n\n파이프라인이 예기치 않게 종료되었습니다. 로그 요약을 확인해 주세요."
        send_telegram_report(error_msg)


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM Hybrid News Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py nlm_orchestrator.py --mode A --full          # 전체 실행 (메가트렌드 모드)
  py nlm_orchestrator.py --mode B --phase 1       # Phase 1만 (개별 기사 모드)
  py nlm_orchestrator.py --phase 2                # Phase 2만 (다운로드 & 게시)
  py nlm_orchestrator.py --mode A --limit 5       # 카테고리당 5개만 수집
        """
    )
    parser.add_argument("--mode", type=str, default="A", choices=["A", "B", "C"],
                        help="운영 모드: A=메가트렌드, B=개별기사, C=하이브리드")
    parser.add_argument("--limit", type=int, default=15,
                        help="카테고리당 수집할 기사 수 (기본: 15)")
    parser.add_argument("--phase", type=int, default=0, choices=[0, 1, 2],
                        help="실행할 Phase (0=전체, 1=수확만, 2=게시만)")
    parser.add_argument("--source", type=str, default="rss", choices=["rss", "db"],
                        help="데이터 소스: rss=실시간 수집, db=히스토리 DB")
    parser.add_argument("--full", action="store_true",
                        help="전체 파이프라인 실행 (Phase 1 → 대기 → Phase 2)")
    parser.add_argument("--poll", type=int, default=60,
                        help="Phase 2 상태 확인 간격 (초, 기본: 60)")
    parser.add_argument("--max-wait", type=int, default=900,
                        help="Phase 2 최대 대기 시간 (초, 기본: 900)")
    
    args = parser.parse_args()
    
    if args.full or args.phase == 0:
        run_full_pipeline(mode=args.mode, limit=args.limit, source=args.source,
                         poll_interval=args.poll, max_wait=args.max_wait)
    elif args.phase == 1:
        run_phase1(mode=args.mode, limit=args.limit, source=args.source)
    elif args.phase == 2:
        run_phase2()


if __name__ == "__main__":
    main()
