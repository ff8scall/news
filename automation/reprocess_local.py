import os
from notebooklm_publisher import NotebookLMPublisher

def reprocess():
    pub = NotebookLMPublisher()
    reports = {
        "ai": "scratch/premium_reports/ai_report.md",
        "hardware": "scratch/premium_reports/hardware_report.md",
        "insights": "scratch/premium_reports/insights_report.md"
    }
    
    for cat, path in reports.items():
        if os.path.exists(path):
            print(f"--- Processing {cat} from {path} ---")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            pub._publish_mode_b(content, cat, {})
        else:
            print(f"Skipping {cat}: {path} not found")

if __name__ == "__main__":
    reprocess()
