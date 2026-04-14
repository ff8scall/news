import os
import re
import sys
import logging
from datetime import datetime

# 상위 디렉토리 참조
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualTranslator")

def translate_strictly(en_content):
    writer = AIWriter()
    
    prompt = f"""
[TASK]
You are a top-tier technical translator. Translate the provided English technical guide into professional Korean.

[STRICT RULES - NO EXCEPTIONS]
1. 1:1 MAPPING: You MUST translate every single sentence, section, and line. DO NOT summarize. DO NOT skip code blocks.
2. NO EMOJIS: Absolutely zero emojis. Use only standard text and Markdown markers (##, ###, *, -).
3. NO META-TALK: Do not include phrases like "I have translated...", "Self-correction...", or "Note: Original code is...". Output ONLY the translated Markdown.
4. CODE PRESERVATION: Preserve all code blocks, variable names, and technical terms exactly as they are in the English version.
5. TONE: Use a highly professional Korean technical tone (~하십시오, ~입니다).

[SOURCE DOCUMENT (ENGLISH)]
{en_content}
"""
    # 번역량이 많으므로 최대 토큰을 보장하기 위해 반복 호출하거나 큰 모델 사용 고려
    # 여기서는 gemma4:latest의 성능을 믿고 한 번에 요청
    ko_content = writer.generate_content(prompt, model="gemma4:latest")
    
    # 클리닝 작업
    if ko_content.startswith("```"):
        ko_content = re.sub(r'^```(markdown)?\n', '', ko_content)
        ko_content = re.sub(r'\n```$', '', ko_content)
    if "---" in ko_content:
        ko_content = ko_content[ko_content.find("---"):]
    
    # 이모지 강제 제거
    ko_content = re.sub(r'[\U00010000-\U0010ffff]', '', ko_content)
    # 메타 발언 패턴 강제 제거
    ko_content = re.sub(r'\(Decision.*?\)', '', ko_content)
    ko_content = re.sub(r'\(Self-Correction.*?\)', '', ko_content)
    
    return ko_content

def main():
    en_path = "content/en/posts/2026/04/14/fastapi-gemini-news-summarizer-v2.md"
    ko_path = "content/ko/posts/2026/04/14/fastapi-gemini-news-summarizer-v2.md"
    
    with open(en_path, "r", encoding="utf-8-sig") as f:
        en_md = f.read()
    
    print("--- [재번역] 1:1 정밀 번역 시작 (생략 엄금) ---")
    ko_md = translate_strictly(en_md)
    
    with open(ko_path, "w", encoding="utf-8-sig") as f:
        f.write(ko_md)
    
    print(f"--- [성공] 번역 완료: {ko_path} ---")

if __name__ == "__main__":
    main()
