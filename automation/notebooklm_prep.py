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
    "각 기사를 독립적으로 분석하여 아래의 구조화된 데이터 형식으로 출력하십시오. "
    "모든 KOR_* 필드는 반드시 한국어로 작성해야 합니다.\n\n"
    "[분류 규칙 - 반드시 준수]\n"
    "1. CLUSTER: 아래 4가지 중 기사 내용과 가장 잘 맞는 하나를 선택\n"
    "   - ai-models-tools: AI 모델, 도구, LLM, 챗봇, AI 트렌드 및 일반 소프트웨어 기사\n"
    "   - gpu-hardware: GPU, 반도체(HBM, NVLink 등), CPU, 서버 인프라, PC 하드웨어 기사\n"
    "   - ai-gaming: 게임 엔진(DLSS, FSR 등), 최적화 기술, AI 게임 플레이, 그래픽 기술 기사\n"
    "   - guides: 튜토리얼, 성능 비교(Benchmark), 팁, 사용 가이드성 기사\n"
    "2. CATEGORY: CLUSTER에 속하는 세부 카테고리 중 하나 선택\n"
    "   - ai-models-tools 소속: ai-models, ai-tools\n"
    "   - gpu-hardware 소속: gpu-chips, pc-robotics\n"
    "   - ai-gaming 소속: game-optimization, ai-gameplay\n"
    "   - guides 소속: tutorials, compare\n\n"
    "---ARTICLE_START---\n"
    "ID: [순번]\n"
    "ENG_TITLE: [English Title]\n"
    "KOR_TITLE: [한국어 제목]\n"
    "CLUSTER: [선택한 CLUSTER 이름]\n"
    "CATEGORY: [선택한 CATEGORY 이름]\n"
    "ENG_SUMMARY: [English Summary]\n"
    "KOR_SUMMARY:\n- [한국어 요약 1]\n- [한국어 요약 2]\n- [한국어 요약 3]\n"
    "ENG_CONTENT: [Detailed English Body]\n"
    "KOR_CONTENT: [한국어 심층 분석 본문, 1,500자 이상, 전문적 저널리즘 문체. 반드시 3~4문장마다 문단 구분 빈 줄을 삽입하여 가독성을 높일 것]\n"
    "KOR_INSIGHT: [한국어 전문가 비평]\n"
    "KEYWORDS_EN: [English Keywords]\n"
    "KEYWORDS_KR: [한국어 키워드]\n"
    "IMAGE_PROMPT: [High-tech minimalist image prompt in English]\n"
    "---ARTICLE_END---"
)

# 모드 C: 하이브리드 (영문 분석만 요청)
PROMPT_MODE_C = (
    "You are a Bloomberg/Reuters senior tech analyst. "
    "Analyze each source article independently and output ONLY structured data. "
    "Strictly follow the Cluster/Category rules provided below.\n\n"
    "[Classification Rules]\n"
    "- ai-models-tools (Category: ai-models, ai-tools): AI trends, software, LLMs.\n"
    "- gpu-hardware (Category: gpu-chips, pc-robotics): Semiconductors, hardware infra.\n"
    "- ai-gaming (Category: game-optimization, ai-gameplay): Gaming tech, optimization.\n"
    "- guides (Category: tutorials, compare): How-to, comparisons.\n\n"
    "---ARTICLE_START---\n"
    "ID: [number]\n"
    "TITLE: [SEO-optimized analytical title]\n"
    "CLUSTER: [selected cluster name]\n"
    "CATEGORY: [selected category name]\n"
    "SUMMARY: [1-sentence executive summary]\n"
    "CONTENT: [Full analytical report, 500+ words, markdown ## sections, cold analytical tone. Insert empty lines between paragraphs for readability.]\n"
    "KEYWORDS: [3 keywords, comma-separated]\n"
    "IMAGE_PROMPT: [High-tech minimalist thumbnail generation prompt]\n"
    "---ARTICLE_END---"
)


class NotebookLMApp:
    """Python wrapper for the notebooklm-mcp CLI tool (nlm)"""
    def __init__(self):
        self.cmd_base = [self._find_nlm_cmd()]
    
    def _find_nlm_cmd(self):
        """nlm 명령어가 PATH에 없으면 윈도우 기본 설치 경로 확인"""
        import shutil
        cmd = shutil.which("nlm")
        if cmd:
            return "nlm"
        
        # Windows fallback
        fallback = r"C:\Users\ff8sc\AppData\Local\Programs\Python\Python313\Scripts\nlm.exe"
        if os.path.exists(fallback):
            return fallback
            
        return "nlm" # Final fallback
    
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
            logger.error(f"[NLM ERROR] Command failed: {' '.join(cmd)}\n{e.stderr}")
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


def process_macro_synthesis(limit_per_cat=15, mode="A", source="rss"):
    """
    NotebookLM 매크로 합성 파이프라인 Phase 1: 데이터 준비 → NLM 업로드 → 리포트 생성 트리거
    
    Args:
        limit_per_cat: 카테고리당 수집할 기사 수
        mode: 운영 모드 ("A", "B", "C")
        source: 데이터 소스 ("rss" 또는 "db")
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
        category_files = harvester.dump_to_category_files(limit_per_cat=limit_per_cat)
    
    jobs_file = "automation/premium_jobs.json"
    active_jobs = {}
    
    if not category_files:
        logger.error(" [!] No category files generated.")
        return False
    
    # 2. 프롬프트 선택
    prompt = get_prompt_for_mode(mode)
    logger.info(f" [2] Selected Mode {mode.upper()} prompt ({len(prompt)} chars)")
    
    # 3. NotebookLM 자동화
    logger.info(f" [3] Bootstrapping NLM Automation... ({len(category_files)} categories)")
    app = NotebookLMApp()
    
    for cat, filepath in category_files.items():
        # 노트북 생성
        title = f"{datetime.now().strftime('%Y-%m-%d')} {cat} Mode-{mode.upper()}"
        notebook = app.create_notebook(title)
        
        if not notebook or 'notebook' not in notebook:
            logger.error(f" Failed to create notebook for {cat}")
            continue
            
        nb_id = notebook['notebook']['id']
        logger.info(f" [OK] Notebook created: {nb_id}")
        
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
    with open(jobs_file, "w", encoding="utf-8") as f:
        json.dump(active_jobs, f, indent=4, ensure_ascii=False)
        
    logger.info(f"\n[PHASE 1 COMPLETE] {len(active_jobs)} reports generating (Mode {mode.upper()}).")
    logger.info("Next: Run notebooklm_publisher.py to download and publish results.")
    return True


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
