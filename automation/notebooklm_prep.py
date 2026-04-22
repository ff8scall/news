import os
import json
import time
import subprocess
import logging
import re
from datetime import datetime
from harvester_v3 import HarvesterV3
from history_manager import HistoryManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NotebookLM_Prep")

# ===================================================================
# 프롬프트 라이브러리
# ===================================================================

# 모드 A: 메가트렌드 에디토리얼 (카테고리별 종합 사설)
PROMPT_MODE_A = (
    "당신은 글로벌 테크 산업 분석가입니다. 업로드된 모든 소스를 분석하여 '2026 테크 메가트렌드 리포트'를 작성하세요.\n"
    "[지시사항]\n"
    "1. 모든 내용은 반드시 한국어(KOREAN)로 작성하십시오.\n"
    "2. 형식: 마크다운. 제목(#), 핵심 요약(리스트), 본문(## 섹션), 에디터 인사이트 포함.\n"
    "3. 분량: 한국어 기준 공백 포함 3,000자 이상의 심층 분석.\n"
    "4. 톤: 전문 저널리즘 수준의 냉철하고 깊이 있는 문체.\n"
    "5. 소스에 있는 팩트만 사용하되, 현시점(2026년 4월)의 맥락을 반영하십시오."
)

# 모드 B: 개별 기사 고품질 생산 (구조화된 데이터 출력)
PROMPT_MODE_B = (
    "당신은 테크 저널리즘 전문가입니다. 업로드된 소스 데이터를 바탕으로 **각 기사를 독립적으로 분석**하여 아래의 [출력 형식]을 **한 글자도 틀리지 말고 엄격하게** 지켜서 출력하십시오.\n\n"
    "[필독: 철저 준수 사항]\n"
    "1. **언어 규정**: 한국어 필드(KOR_...)는 반드시 **한국어**로, 영어 필드(ENG_...)는 반드시 **영어**로 작성하십시오.\n"
    "2. **필드 누락 절대 금지**: KOR_TITLE, KOR_SUMMARY, KOR_CONTENT, ENG_TITLE, ENG_CONTENT 등 모든 필드는 어떤 경우에도 누락되어서는 안 됩니다. 소스가 부족하면 분석을 통해 내용을 채우십시오.\n"
    "3. **구분자 형식 고수**: 각 기사의 시작과 끝에 ---ARTICLE_START--- 와 ---ARTICLE_END---를 명확히 표시하십시오. 구분자 라인에는 다른 텍스트(예: **, #)를 섞지 마십시오.\n"
    "4. **필드 표기**: '**필드명:** 내용' 형식을 엄격히 지키십시오. 필드명은 대문자로 쓰고 반드시 볼드(**) 처리하십시오.\n"
    "5. **이미지 추출**: 소스 데이터에 `Image URL` 또는 `ORIGINAL_IMAGE`가 명시되어 있다면 반드시 `ORIGINAL_IMAGE:` 필드에 정확히 기재하십시오.\n\n"
    "[출력 형식]\n"
    "---ARTICLE_START---\n"
    "**ID:** [순번]\n"
    "**ENG_TITLE:** [SEO-optimized English Title]\n"
    "**KOR_TITLE:** [한국어 핵심 제목]\n"
    "**CLUSTER:** [ai | hardware | insights]\n"
    "**CATEGORY:** [chips | models | apps | high-end | analysis | guide]\n"
    "**ENG_SUMMARY:** [Professional English Summary]\n"
    "**KOR_SUMMARY:**\n- [한국어 요약 1]\n- [한국어 요약 2]\n- [한국어 요약 3]\n"
    "**ENG_CONTENT:** [Detailed English Synthesis & Analysis, 500+ words]\n"
    "**KOR_CONTENT:** [한국어 심층 분석 본문, 1,200자 내외, 마크다운 ## 소제목 활용]\n"
    "**KOR_INSIGHT:** [한국어 전문가 시사점 및 미래 비평]\n"
    "**KEYWORDS_EN:** [English Keywords, comma separated]\n"
    "**KEYWORDS_KR:** [한국어 키워드, 콤마 구분]\n"
    "**IMAGE_PROMPT:** [Detailed High-tech image prompt in English]\n"
    "**ORIGINAL_IMAGE:** [Source Image URL if exists, else 'None']\n"
    "---ARTICLE_END---"
)


# 모드 C: 하이브리드 (영문 분석만 요청)
PROMPT_MODE_C = (
    "Analyze each source article independently and output ONLY structured data. **STRICT FORMATTING REQUIRED.**\n\n"
    "[FORMAT RULES]\n"
    "1. NO BULLETS or BOLD on delimiters like ---ARTICLE_START---.\n"
    "2. Fields must follow EXACTLY the template below.\n\n"
    "---ARTICLE_START---\n"
    "ID: [number]\n"
    "TITLE: [SEO-optimized analytical title]\n"
    "CLUSTER: [selected cluster name]\n"
    "CATEGORY: [selected category name]\n"
    "SUMMARY: [1-sentence executive summary]\n"
    "CONTENT: [Full analytical report, 500+ words, markdown ## sections]\n"
    "KEYWORDS: [3 keywords]\n"
    "IMAGE_PROMPT: [High-tech minimalist thumbnail generation prompt]\n"
    "ORIGINAL_IMAGE: [Extract the 'Original Top Image' URL from source if available, else 'None']\n"
    "---ARTICLE_END---"
)


class NotebookLMApp:
    """Python wrapper for the notebooklm-mcp CLI tool (nlm)"""
    def __init__(self):
        self.cmd_base = [self._find_nlm_cmd()]
    
    def _find_nlm_cmd(self):
        """[V2.8] venv 환경 대응: nlm 명령어가 PATH에 없으면 파이썬 실행 파일 경로 주변 확인"""
        import shutil
        import sys
        
        # 1. PATH에서 먼저 확인
        cmd = shutil.which("nlm")
        if cmd:
            return cmd
        
        # 2. 현재 가상환경(venv/bin) 내 확인 (Linux/Ubuntu 최우선)
        bin_dir = os.path.dirname(sys.executable)
        venv_nlm = os.path.join(bin_dir, "nlm")
        if os.path.exists(venv_nlm):
            return venv_nlm
            
        # 3. Windows fallback
        fallback = r"C:\Users\ff8sc\AppData\Local\Programs\Python\Python313\Scripts\nlm.exe"
        if os.path.exists(fallback):
            return fallback
            
        return "nlm" # Final fallback
    
    def login(self):
        """[V2.1] nlm login 명령어를 실행하여 브라우저 인증을 유도합니다."""
        logger.info("=" * 60)
        logger.info(" [AUTH] Initiating NotebookLM Login...")
        logger.info(" [AUTH] A browser window should open. Please approve the connection.")
        logger.info("=" * 60)
        try:
            # 윈도우 환경에서 브라우저가 잘 뜨도록 직접 실행
            res = subprocess.run(self.cmd_base + ["login"], capture_output=False, text=True)
            if res.returncode == 0:
                logger.info(" [AUTH] Login command executed. Waiting for session to be active...")
                time.sleep(2) # 짧은 유예 시간
                return True
        except Exception as e:
            logger.error(f" [AUTH] Login failed: {e}")
        return False

    def verify_auth(self):
        """[V2.7] 현재 세션의 유효성을 검사합니다."""
        logger.info(" [AUTH] Verifying NotebookLM session...")
        # studio status는 인증이 필요하므로 유효성 체크용으로 적합
        # 존재하지 않는 ID라도 인증 에러는 먼저 뜸. 
        # subprocess.run을 직접 호출하여 상세 제어
        cmd = self.cmd_base + ["studio", "status", "verify-session-dummy-id"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            err_msg = res.stderr or res.stdout or ""
            if "Authentication expired" in err_msg or "Authentication Error" in err_msg:
                return False
            # NOT_FOUND나 다른 에러가 나더라도 '인증 에러'가 아니면 유효한 세션으로 간주
            return True
        except:
            return False

    
    def run_cmd(self, args, use_json=False):
        cmd = self.cmd_base + args
        if use_json:
            cmd.append("--json")
            
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8")
            output = res.stdout.strip()
            if use_json:
                return json.loads(output)
            return output
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr or e.stdout or ""
            logger.error(f"[NLM ERROR] Command failed: {' '.join(cmd)}\n{err_msg}")
            
            # [V2.6] 인증 만료 감지 및 텔레그램 알림
            if "Authentication expired" in err_msg or "Authentication Error" in err_msg:
                from common_utils import send_telegram_report
                alert_msg = "⚠️ <b>[NotebookLM 인증 만료]</b>\n세션이 종료되었습니다. 터미널에서 <code>nlm login</code>을 실행하여 재인증해 주세요."
                send_telegram_report(alert_msg)
                logger.error("Authentication expired notification sent to Telegram.")
            
            return None
        except Exception as e:
            logger.error(f"[NLM ERROR] {e}")
            return None


    def create_notebook(self, title):
        logger.info(f"Creating notebook: {title}")
        res = self.run_cmd(["create", "notebook", title], use_json=False)
        if res:
            # ID 추출: ID: (uuid)
            match = re.search(r"ID:\s*([a-f0-9-]+)", res, re.I)
            if match:
                nb_id = match.group(1)
                return {"notebook": {"id": nb_id}}
        return None

    def add_source(self, notebook_id, filepath):
        logger.info(f"Adding source to {notebook_id}: {filepath}")
        res = self.run_cmd(["source", "add", notebook_id, "--file", filepath], use_json=False)
        if res:
            # ID 추출: ID: (uuid)
            match = re.search(r"ID:\s*([a-f0-9-]+)", res, re.I)
            if match:
                return {"source": {"id": match.group(1)}}
        return None

    def create_report(self, notebook_id, prompt):
        """범용 리포트 생성: 프롬프트를 외부에서 주입"""
        logger.info(f"Creating report for notebook {notebook_id}")
        # Note: --format "Create Your Own" requires --prompt
        return self.run_cmd(["create", "report", notebook_id, "--format", "Create Your Own", "--prompt", prompt, "-y"], use_json=False)

    def create_audio_podcast(self, notebook_id):
        logger.info(f"Creating Audio Podcast Overview for notebook {notebook_id}")
        return self.run_cmd(["create", "audio", notebook_id, "-y"], use_json=False)
        
    def check_status(self, notebook_id):
        # status artifacts는 --json 지원 가능성 높음
        return self.run_cmd(["status", "artifacts", notebook_id], use_json=True)

    def get_latest_report(self, notebook_id):
        """[V2.5] 스튜디오 아티팩트 목록에서 가장 최신 리포트 정보를 가져옵니다."""
        try:
            # studio status 명령어로 아티팩트 목록 조회
            res = self.run_cmd(["studio", "status", notebook_id], use_json=True)
            if res and isinstance(res, list):
                # 리포트 타입만 필터링
                reports = [a for a in res if a.get("type", "").lower() == "report"]
                if reports:
                    # ID가 있으면 성공
                    return reports[0] # 첫 번째가 최신이라고 가정 (혹은 정렬 필요)
        except Exception as e:
            logger.error(f"Error getting latest report: {e}")
        return None

    def download_report(self, notebook_id, artifact_id=None):
        """[V2.5] 리포트 아티팩트를 다운로드하여 텍스트로 반환합니다."""
        import tempfile
        import uuid
        
        tmp_name = f"nlm_report_{uuid.uuid4().hex}.md"
        tmp_path = os.path.join(tempfile.gettempdir(), tmp_name)
        
        args = ["download", "report", notebook_id, "-o", tmp_path]
        if artifact_id:
            args.extend(["--id", artifact_id])
            
        res = self.run_cmd(args, use_json=False)
        if os.path.exists(tmp_path):
            try:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    content = f.read()
                os.remove(tmp_path)
                return content
            except Exception as e:
                logger.error(f"Error reading downloaded report: {e}")
        return None


def get_prompt_for_mode(mode):
    """운영 모드에 따른 프롬프트 반환"""
    prompts = {
        "A": PROMPT_MODE_A,
        "B": PROMPT_MODE_B,
        "C": PROMPT_MODE_C,
    }
    return prompts.get(mode.upper(), PROMPT_MODE_A)


def dump_db_to_category_files(limit_per_cat=15):
    """[V4.1] DB 히스토리에서 기사를 읽어 카테고리별 마크다운 생성"""
    db = HistoryManager()
    # 최근 처리된 기사들 가져오기 (가급적 넉넉히)
    recent_items = db.get_recent_posts(limit=limit_per_cat * 10)
    
    # 카테고리별 그룹화 (DB에는 카테고리 정보가 없으므로 harvester의 분류 로직이 필요할 수 있음)
    # 하지만 현재 HistoryManager.get_recent_posts는 title, local_url만 반환함.
    # 일단 전체를 하나의 파일로 만들거나, DB에서 더 많은 정보를 가져오도록 HistoryManager를 보완해야 함.
    
    # 임시: 모든 최근 기사를 하나의 'all' 카테고리로 묶음 (또는 DB 스키마 확인 필요)
    # DB에는 url, title, local_url, processed_at만 있음. 
    # 카테고리 정보를 알 수 없으므로, NotebookLM이 직접 분류하도록 단일 소스 파일로 제공하는 것이 나을 수 있음.
    
    os.makedirs("scratch", exist_ok=True)
    filepath = "scratch/db_history_dump.md"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# LEGO-SIA Historical Intelligence Source Data\n")
        f.write(f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Articles:** {len(recent_items)}\n\n")
        
        for idx, a in enumerate(recent_items, 1):
            f.write("--------------------------------------------------\n")
            f.write(f"## [History {idx}] {a.get('title', 'Untitled')}\n")
            f.write(f"- **URL:** {a.get('url', 'N/A')}\n\n")
            # Note: DB에는 본문이 없으므로 제목 위주로 분석하거나, 
            # 나중에 DB 스키마를 확장하여 요약/본문을 저장해야 함.
            
    return {"history": filepath}


def _split_articles_into_batches(category_files, threshold=8):
    """[V6.2] 기사 목록이 너무 길면 잘게 쪼개어 NLM의 출력 안정성을 보장합니다."""
    split_files = {}
    for cat, filepath in category_files.items():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # [V6.3] 기사 구분선(---)을 기준으로 기사 분리 시도 (유연한 매칭 지원)
            articles_text = "".join(lines).split("\n---\n")
            # 헤더 제외 실질 기사 추출
            content_articles = [a.strip() for a in articles_text if "## " in a]
            
            if len(content_articles) > threshold:
                logger.info(f" [SPLIT] {cat} has {len(content_articles)} articles. Splitting into batches...")
                # 절반씩 나눔 (더 많으면 3개로 나눌수도 있지만 일단 2분할)
                mid = (len(content_articles) + 1) // 2
                batches = [content_articles[:mid], content_articles[mid:]]
                
                for i, batch in enumerate(batches, 1):
                    split_cat = f"{cat}_part{i}"
                    split_path = filepath.replace(".md", f"_p{i}.md")
                    with open(split_path, "w", encoding="utf-8") as f:
                        f.write(f"# {cat.upper()} Intelligence - Part {i}\n\n")
                        f.write("--------------------------------------------------\n".join(batch))
                    split_files[split_cat] = split_path
            else:
                split_files[cat] = filepath
        except Exception as e:
            logger.error(f"Failed to split articles for {cat}: {e}")
            split_files[cat] = filepath
            
    return split_files


def process_macro_synthesis(limit_per_cat=15, mode="A", source="rss"):
    """
    NotebookLM 매크로 합성 파이프라인 Phase 1: 데이터 준비 → NLM 업로드 → 리포트 생성 트리거
    [V6.2] Smart Job Split 적용 (기사 과다 시 자동 분할)
    """
    logger.info("=" * 50)
    logger.info(f"  [START] Premium Pipeline (Mode {mode.upper()}, Source {source.upper()})")
    logger.info("=" * 50)
    
    # 1. 뉴스 데이터 확보
    if source.lower() == "db":
        logger.info(" [1] Fetching articles from History DB...")
        category_files = dump_db_to_category_files(limit_per_cat=limit_per_cat)
    else:
        logger.info(" [1] Harvesting raw articles from RSS...")
        harvester = HarvesterV3()
        # [V6.2] 수집은 넉넉히(12개) 하되, 나중에 8개 단위로 쪼갬
        category_files = harvester.dump_to_category_files(limit_per_cat=limit_per_cat)
    
    if not category_files:
        logger.error(" [!] No category files generated.")
        return False

    # [V6.3] 기사 수에 따른 자동 분할 로직 (Job Splitting)
    # NLM 안정성을 위해 임계값을 8에서 5로 하향 (기사가 6개 이상이면 분할)
    final_category_files = _split_articles_into_batches(category_files, threshold=5)
    
    jobs_file = "automation/premium_jobs.json"
    active_jobs = {}
    
    # 2. 프롬프트 선택
    prompt = get_prompt_for_mode(mode)
    logger.info(f" [2] Selected Mode {mode.upper()} prompt ({len(prompt)} chars)")
    
    # 3. NotebookLM 자동화
    logger.info(f" [3] Bootstrapping NLM Automation... ({len(final_category_files)} jobs)")
    app = NotebookLMApp()
    
    for cat, filepath in final_category_files.items():
        # 노트북 생성
        # [V6.2] 독립된 제목 유지 (Part 표시 제거 요청 반영 - 파일명엔 있지만 제목에선 최소화)
        clean_cat = cat.replace("_part1", "").replace("_part2", "")
        title = f"{datetime.now().strftime('%Y-%m-%d')} {clean_cat} Analysis"
        # 중복 제목 방지를 위해 고유 ID 추가
        if "_part" in cat:
            title += f" ({cat.split('_')[-1]})"
            
        notebook = app.create_notebook(title)
        
        if not notebook or 'notebook' not in notebook:
            logger.error(f" Failed to create notebook for {cat}")
            continue
            
        nb_id = notebook['notebook']['id']
        logger.info(f" [OK] Notebook created: {nb_id} ({title})")
        
        # 소스 추가
        source_res = app.add_source(nb_id, filepath)
        logger.info(f" [OK] Source added. Triggering report...")
        
        # 리포트 생성 트리거
        report_res = app.create_report(nb_id, prompt)
        if report_res:
            logger.info(f" [OK] Report triggered for {cat} (Mode {mode.upper()})")
            active_jobs[cat] = {
                "notebook_id": nb_id,
                "title": title,
                "mode": mode.upper(),
                "status": "pending",
                "triggered_at": datetime.now().isoformat()
            }
    
    # Job 상태 저장
    # [V6.4] 기존 Job이 있으면 유지하면서 병합(Merge)
    try:
        if os.path.exists(jobs_file):
            with open(jobs_file, "r", encoding="utf-8") as f:
                existing_jobs = json.load(f)
                # 새로운 작업으로 업데이트 (기존 다른 카테고리는 보존)
                existing_jobs.update(active_jobs)
                active_jobs = existing_jobs
    except Exception as e:
        logger.warning(f"Failed to merge existing jobs: {e}")

    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(active_jobs, f, indent=4, ensure_ascii=False)
        
    logger.info(f"\n[PHASE 1 COMPLETE] {len(active_jobs)} reports generating (Mode {mode.upper()}).")
    return active_jobs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NotebookLM Premium Pipeline - Phase 1 (Prep)")
    parser.add_argument("--limit", type=int, default=15, help="Articles per category to harvest")
    parser.add_argument("--mode", type=str, default="A", choices=["A", "B", "C"],
                        help="Operation mode: A=Megatrend Editorial, B=Individual Articles, C=Hybrid EN-only")
    parser.add_argument("--source", type=str, default="rss", choices=["rss", "db"],
                        help="Data source: rss=Fresh Harvesting, db=History Database")
    args = parser.parse_args()
    
    process_macro_synthesis(limit_per_cat=args.limit, mode=args.mode, source=args.source)


def process_macro_synthesis_v2(limit_per_cat=15, mode="B", source="rss"):
    """
    [V2.1] NotebookLM Macro-Synthesis with INTEGRATED source (V2 logic)
    - 모든 기사를 하나로 통합하여 NLM에 업로드
    - NLM이 스스로 카테고리를 분류하게 함
    """
    from v2.harvester_v4 import HarvesterV4
    
    logger.info("=" * 60)
    logger.info(f"  [START V2.1] Integrated Premium Pipeline (Mode {mode.upper()})")
    logger.info("=" * 60)
    
    # 1. 뉴스 데이터 확보 (통합 파일 생성)
    logger.info(f" [1] Harvesting & Enriching all articles into a SINGLE source...")
    harvester = HarvesterV4()
    macro_filepath = harvester.dump_to_single_file(limit_per_cat=limit_per_cat)
    
    if not macro_filepath:
        logger.error(" [!] Failed to generate integrated macro source.")
        return False
        
    jobs_file = "automation/premium_jobs.json"
    active_jobs = {}
    
    # 2. 프롬프트 선택
    prompt = get_prompt_for_mode(mode)
    
    # 3. NotebookLM 자동화 (단일 노트북 생성)
    app = NotebookLMApp()
    title = f"[V2.1] {datetime.now().strftime('%Y-%m-%d')} Daily Macro-Intelligence"
    notebook = app.create_notebook(title)
    
    if not notebook or 'notebook' not in notebook:
        logger.error(" Failed to create macro notebook")
        return False
        
    nb_id = notebook['notebook']['id']
    logger.info(f" [V2.1 OK] Macro Notebook created: {nb_id}")
    
    # 소스 추가
    app.add_source(nb_id, macro_filepath)
    logger.info(f" [V2.1 OK] Integrated source added. Triggering report...")
    
    # 리포트 생성 트리거
    report_res = app.create_report(nb_id, prompt)
    if report_res:
        logger.info(f" [V2.1 OK] Macro Report triggered (Mode {mode.upper()})")
        # 'macro'라는 가상 카테고리로 저장하되, 나중에 publisher가 실제 기사별 카테고리로 분산함
        active_jobs["daily_macro"] = {
            "notebook_id": nb_id,
            "title": title,
            "mode": mode.upper(),
            "status": "pending",
            "triggered_at": datetime.now().isoformat()
        }
    
    # Job 상태 저장
    try:
        if os.path.exists(jobs_file):
            with open(jobs_file, "r", encoding="utf-8") as f:
                existing_jobs = json.load(f)
                existing_jobs.update(active_jobs)
                active_jobs = existing_jobs
    except: pass

    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(active_jobs, f, indent=4, ensure_ascii=False)
        
    logger.info(f"\n[V2.1 PHASE 1 COMPLETE] Integrated macro report generating.")
    return True
