import os
import re
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def final_fix():
    en_path = "content/en/guides/2026/04/14/Claude-3-API-Integration-with-Local-RAG-Systems.md"
    ko_path = "content/ko/guides/2026/04/14/Claude-3-API-Integration-with-Local-RAG-Systems.md"
    
    writer = AIWriter()
    with open(en_path, "r", encoding="utf-8-sig") as f:
        en_md = f.read()
    
    prompt = f"[TASK] High-quality Professional Korean Translation (Strictly NO EMOJIS)\n\n[SOURCE]\n{en_md}"
    ko_md = writer.generate_content(prompt, model="gemma4:latest")
    
    if "---" in ko_md:
        ko_md = ko_md[ko_md.find("---"):]
    ko_md = re.sub(r'[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s.,;:!?()\[\]{}<>#*~\-_/`\'"]', '', ko_md)
    
    os.makedirs(os.path.dirname(ko_path), exist_ok=True)
    with open(ko_path, "w", encoding="utf-8-sig") as f:
        f.write(ko_md)
    print(f"[최종 미션 완료] Claude-3 Korean guide created.")

if __name__ == "__main__":
    final_fix()
