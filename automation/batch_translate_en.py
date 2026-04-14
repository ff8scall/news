import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def translate_to_en(ko_path, en_path):
    writer = AIWriter()
    with open(ko_path, "r", encoding="utf-8-sig") as f:
        ko_md = f.read()
    
    prompt = f"""
[TASK]
Translate this Korean technical guide into high-quality professional English.

[STRICT RULES]
1. ZERO EMOJIS.
2. YAML PRESERVATION: Keep original YAML structure.
3. TONE: Professional tech blog/documentation tone.
4. FORMAT: Maintain all code blocks and markdown structure.

[SOURCE]
{ko_md}
"""
    en_md = writer.generate_content(prompt, model="gemma4:latest")
    
    # 클리닝
    if en_md.startswith("```"):
        en_md = re.sub(r'^```(markdown)?\n', '', en_md)
        en_md = re.sub(r'\n```$', '', en_md)
    if "---" in en_md:
        en_md = en_md[en_md.find("---"):]

    os.makedirs(os.path.dirname(en_path), exist_ok=True)
    with open(en_path, "w", encoding="utf-8-sig") as f:
        f.write(en_md)
    print(f"[EN 번역 완료] {os.path.basename(en_path)}")

def main():
    # 감사 결과 기반 누락 가이드 (KO -> EN)
    # paths based on audit: content/ko/guides/2026/04/14/
    missing_in_en = [
        "guides/2026/04/14/DeepSeek-V3-VSCode-Setup.md",
        "posts/2026/04/14/fastapi-gemini-news-summarizer.md"
    ]
    
    for rel_path in missing_in_en:
        ko_file = os.path.join("content/ko", rel_path)
        en_file = os.path.join("content/en", rel_path)
        if os.path.exists(ko_file):
            translate_to_en(ko_file, en_file)

if __name__ == "__main__":
    main()
