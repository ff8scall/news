import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def force_translate(en_rel_path):
    en_path = os.path.join("content/en/posts", en_rel_path)
    ko_path = os.path.join("content/ko/posts", en_rel_path)
    
    if not os.path.exists(en_path):
        print(f"EN File not found: {en_path}")
        return

    writer = AIWriter()
    with open(en_path, "r", encoding="utf-8-sig") as f:
        en_md = f.read()
    
    prompt = f"[TASK] Professional Korean Translation (No Emojis)\n\n[SOURCE]\n{en_md}"
    ko_md = writer.generate_content(prompt, model="gemma4:latest")
    
    # Cleaning
    if "---" in ko_md:
        ko_md = ko_md[ko_md.find("---"):]
    ko_md = re.sub(r'[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s.,;:!?()\[\]{}<>#*~\-_/`\'"]', '', ko_md)
    
    os.makedirs(os.path.dirname(ko_path), exist_ok=True)
    with open(ko_path, "w", encoding="utf-8-sig") as f:
        f.write(ko_md)
    print(f"[강제 완료] {en_rel_path}")

# Run for the last 2 missing
force_translate("2026/04/13/amd-and-samsung-forge-strategic-partnership-for-ne-40d6eb.md")
force_translate("2026/04/14/Claude-3-API-Integration-with-Local-RAG-Systems.md")
