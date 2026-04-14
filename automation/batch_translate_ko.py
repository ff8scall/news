import os
import re
import sys
from datetime import datetime

# 상위 디렉토리 참조하여 AIWriter 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def translate_article(en_path, ko_path):
    writer = AIWriter()
    with open(en_path, "r", encoding="utf-8-sig") as f:
        en_md = f.read()
    
    prompt = f"""
[TASK]
Translate this English technical article into professional Korean.

[STRICT RULES]
1. ZERO EMOJIS: Use no emojis.
2. 1:1 CLONE: Do not omit any sections or code blocks.
3. YAML PRESERVATION: Keep YAML keys (title, date, etc.) in English, but translate their values (title, description).
4. TONE: Professional tech magazine style (~입니다).

[SOURCE]
{en_md}
"""
    ko_md = writer.generate_content(prompt, model="gemma4:latest")
    
    # 클리닝
    if ko_md.startswith("```"):
        ko_md = re.sub(r'^```(markdown)?\n', '', ko_md)
        ko_md = re.sub(r'\n```$', '', ko_md)
    if "---" in ko_md:
        ko_md = ko_md[ko_md.find("---"):]
    
    ko_md = re.sub(r'[^\x00-\x7F가-힣ㄱ-ㅎㅏ-ㅣ\s.,;:!?()\[\]{}<>#*~\-_/`\'"]', '', ko_md)
    
    # 디렉토리 생성 및 저장
    os.makedirs(os.path.dirname(ko_path), exist_ok=True)
    with open(ko_path, "w", encoding="utf-8-sig") as f:
        f.write(ko_md)
    print(f"[번역 완료] {os.path.basename(ko_path)}")

def main():
    # 감사 결과 기반 누락 기사 리스트 (EN -> KO)
    missing_in_ko = [
        "2026/04/13/ai-driven-scalability-building-automated-high-yiel-73b8f7.md",
        "2026/04/13/amd-and-samsung-forge-strategic-partnership-for-ne-40d6eb.md",
        "2026/04/13/indias-ai-growth-trajectory-shifting-focus-from-mo-e6af3c.md",
        "2026/04/13/hyper-photonix-16t-silicon-photonics-transceiver-s-812f43.md",
        "2026/04/13/comparative-governance-and-developmental-data-anal-364a51.md",
        "2026/04/13/meta-platforms-structural-realignment-and-the-stra-ddcf40.md"
    ]
    
    for rel_path in missing_in_ko:
        en_file = os.path.join("content/en/posts", rel_path)
        ko_file = os.path.join("content/ko/posts", rel_path)
        if os.path.exists(en_file):
            translate_article(en_file, ko_file)

if __name__ == "__main__":
    main()
