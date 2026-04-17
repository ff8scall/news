# -*- coding: utf-8 -*-
"""
[nlm_orchestrator.py] NotebookLM 하이브리드 뉴스 파이프라인 오케스트레이터
=====================================================================
전체 플로우를 한 번에 실행하거나, Phase별로 분리 실행할 수 있습니다.

사용법:
  # 전체 실행 (수확 → NLM 트리거 → 대기 → 다운로드 → 게시)
  py nlm_orchestrator.py --mode A --full

  # Phase 1만 (수확 → NLM 트리거)
  py nlm_orchestrator.py --mode B --phase 1

  # Phase 2만 (다운로드 → 게시)  
  py nlm_orchestrator.py --phase 2
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# 현재 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from notebooklm_prep import process_macro_synthesis
from notebooklm_publisher import NotebookLMPublisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(current_dir, "nlm_orchestrator.log"), encoding='utf-8')
    ]
)
logger = logging.getLogger("LegoSia.NLM_Orchestrator")


def run_phase1(mode="A", limit=15, source="rss"):
    """Phase 1: 뉴스 데이터 준비 → NotebookLM 리포트 트리거"""
    logger.info("=" * 60)
    logger.info(f"  PHASE 1: Data Prep & Trigger (Mode {mode}, Source {source}, limit={limit})")
    logger.info("=" * 60)
    
    t0 = time.time()
    success = process_macro_synthesis(limit_per_cat=limit, mode=mode, source=source)
    t1 = time.time()
    
    if success:
        logger.info(f"[PHASE 1 OK] Completed in {t1-t0:.1f}s. Reports are generating in NotebookLM.")
    else:
        logger.error("[PHASE 1 FAIL] No categories were processed.")
    
    return success


def run_phase2():
    """Phase 2: NotebookLM 결과물 다운로드 → 파싱 → Hugo 포스트 게시"""
    logger.info("=" * 60)
    logger.info("  PHASE 2: Download & Publish")
    logger.info("=" * 60)
    
    t0 = time.time()
    publisher = NotebookLMPublisher()
    publisher.process_pending_jobs()
    t1 = time.time()
    
    logger.info(f"[PHASE 2 OK] Completed in {t1-t0:.1f}s.")


def run_full_pipeline(mode="A", limit=15, source="rss", poll_interval=60, max_wait=600):
    """
    전체 파이프라인: Phase 1 → 대기 → Phase 2
    
    Args:
        mode: 운영 모드 (A/B/C)
        limit: 카테고리당 수집 기사 수
        source: 데이터 소스 (rss/db)
        poll_interval: 상태 확인 간격 (초)
        max_wait: 최대 대기 시간 (초)
    """
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║  NotebookLM Full Pipeline Orchestrator                   ║")
    logger.info(f"║  Mode: {mode} | Source: {source} | Limit: {limit} ║")
    logger.info(f"║  Started: {datetime.now().strftime('%H:%M:%S')}                                    ║")
    logger.info("╚" + "═" * 58 + "╝")
    
    # Phase 1
    success = run_phase1(mode=mode, limit=limit, source=source)
    if not success:
        logger.error("Pipeline aborted: Phase 1 failed.")
        return
    
    # 대기: NotebookLM이 리포트를 생성할 시간을 줌
    logger.info(f"\n[WAITING] NotebookLM is generating reports...")
    logger.info(f"[WAITING] Will poll every {poll_interval}s, max wait: {max_wait}s")
    
    waited = 0
    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval
        logger.info(f"[POLL] {waited}s elapsed. Checking status...")
        
        # Phase 2 시도 (완료된 것부터 게시)
        publisher = NotebookLMPublisher()
        jobs = publisher.load_jobs()
        
        # 모든 Job이 published 상태인지 확인
        all_done = all(j.get("status") == "published" for j in jobs.values()) if jobs else False
        
        if all_done:
            logger.info("[DONE] All jobs published successfully!")
            break
        
        # 일부만 완료된 경우에도 게시 시도
        publisher.process_pending_jobs()
    
    if waited >= max_wait:
        logger.warning(f"[TIMEOUT] Max wait ({max_wait}s) reached. Some jobs may still be pending.")
        logger.info("Run 'py nlm_orchestrator.py --phase 2' later to publish remaining jobs.")
    
    logger.info("\n[PIPELINE COMPLETE]")


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
    parser.add_argument("--max-wait", type=int, default=600,
                        help="Phase 2 최대 대기 시간 (초, 기본: 600)")
    
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
