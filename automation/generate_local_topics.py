import os
import sys
import json
import re

# AIWriter 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def get_topics(category, count=10):
    writer = AIWriter()
    prompt = f"""
    [TASK]
    Generate {count} unique, high-end technical news headlines for the '{category}' section of a tech magazine.
    Focus on latest trends like HBM4, Next-gen GPUs, UE5.5, AI-driven gaming tech.
    Return ONLY a JSON list of strings (English). No other text.
    """
    response = writer.generate_content(prompt, model="gemma4:latest")
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    # Fallback to lines if JSON fails
    lines = [l.strip() for l in response.strip().split("\n") if len(l.strip()) > 10]
    return lines[:count]

def main():
    print("--- 로컬 Gemma4를 이용한 토픽 생성 시작 ---")
    hw_topics = get_topics("Hardware (GPU, Semiconductor, HBM)", 10)
    gaming_topics = get_topics("Gaming Tech (AI Rendering, Optimization, Engines)", 10)
    
    print(f"Hardware Topics: {len(hw_topics)}")
    print(f"Gaming Topics: {len(gaming_topics)}")
    
    with open("automation/temp_topics.json", "w", encoding="utf-8") as f:
        json.dump({"hardware": hw_topics, "gaming": gaming_topics}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
