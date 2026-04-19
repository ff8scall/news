import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime

# Import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from harvester_v3 import HarvesterV3
from notebooklm_publisher import NotebookLMPublisher

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("LegoSia.Unified")

NLM_PATH = r"C:\Users\ff8sc\AppData\Local\Programs\Python\Python313\Scripts\nlm.exe"
PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "reinforced_prompt.txt")
JOBS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "premium_jobs.json")

class UnifiedWorkflow:
    def __init__(self):
        self.hv = HarvesterV3()
        self.pub = NotebookLMPublisher()
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            self.report_prompt = f.read().strip()

    def run_full_cycle(self):
        logger.info("=== [STAGE 1] Harvesting Latest Tech News ===")
        # Get up to 10 high-quality articles per category
        articles, stats = self.hv.fetch_all(limit_per_cat=10)
        logger.info(f"Harvested {len(articles)} articles: {stats}")

        if not articles:
            logger.info("No new articles found. Cycle ended.")
            return

        with open(JOBS_PATH, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        for cluster_id, job in jobs.items():
            logger.info(f"\n>>> Processing Cluster: {cluster_id.upper()} ({job['notebook_id']})")
            
            # 1. Filter articles for this cluster
            cluster_articles = [a for a in articles if a.eng_category_slug in job['categories']]
            if not cluster_articles:
                logger.info(f"No new articles for {cluster_id}. Skipping.")
                continue

            # 2. Upload Sources
            urls = [a.url for a in cluster_articles]
            logger.info(f"Uploading {len(urls)} sources to NotebookLM...")
            cmd_upload = [NLM_PATH, "source", "add", job['notebook_id']]
            for u in urls:
                cmd_upload.extend(["--url", u])
            cmd_upload.append("--wait")
            
            try:
                subprocess.run(cmd_upload, check=True)
                logger.info("Sources uploaded and processed successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to upload sources for {cluster_id}: {e}")
                continue

            # 3. Trigger Report Generation
            logger.info("Triggering Report Generation with reinforced prompt...")
            cmd_report = [
                NLM_PATH, "report", "create", job['notebook_id'],
                "--format", "Create Your Own",
                "--prompt", self.report_prompt,
                "--confirm"
            ]
            try:
                subprocess.run(cmd_report, check=True)
                logger.info("Report generation triggered.")
                # Give NLM some time to stabilize
                time.sleep(10)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to trigger report for {cluster_id}: {e}")
                continue

            # 4. Publish
            logger.info(f"Downloading and publishing latest report for {cluster_id}...")
            # We reset status to pending to force publisher to check
            job['status'] = 'pending'
            with open(JOBS_PATH, "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=4)
            
            # Run publisher to process the newly pending job
            self.pub.process_pending_jobs()

        logger.info("\n=== Full Automation Cycle Completed Successfully! ===")

if __name__ == "__main__":
    workflow = UnifiedWorkflow()
    workflow.run_full_cycle()
