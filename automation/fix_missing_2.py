import os
import sys
import re

# AIWriter 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_writer import AIWriter

def generate_missing(topic, cluster, category):
    writer = AIWriter()
    print(f"[긴급 집필] {topic}")
    
    # EN
    en_prompt = f"Write a professional technical news article in English about: '{topic}'. ROLE: Senior Tech Journalist. No emojis. Structure: Title, Description, Content (## headers)."
    en_raw = writer.generate_content(en_prompt, model="gemma4:latest")
    
    # KO
    ko_prompt = f"Translate this technical article into professional Korean. Source:\n{en_raw}\nSTRICT: Professional '입니다' style, ZERO emojis. Keep YAML keys in English."
    ko_raw = writer.generate_content(ko_prompt, model="gemma4:latest")
    
    def save(raw, lang):
        slug = re.sub(r'[^a-z0-9]', '-', topic.lower())[:50].strip('-')
        title_match = re.search(r'Title:\s*(.*)', raw)
        title = title_match.group(1).strip('"') if title_match else topic
        
        fm = f'---\ntitle: "{title}"\ndate: "2026-04-14T11:00:00Z"\nclusters: ["{cluster}"]\ncategories: ["{category}"]\ntype: "posts"\n---\n\n'
        content = raw.split("Content:")[-1] if "Content:" in raw else raw
        content = re.sub(r'^```(markdown)?\n', '', content)
        content = re.sub(r'\n```$', '', content)
        
        path = f"content/{lang}/posts/2026/04/14/{slug}.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8-sig") as f: f.write(fm + content.strip())
        print(f"Saved: {path}")

    save(en_raw, "en")
    save(ko_raw, "ko")

if __name__ == "__main__":
    generate_missing("Power Efficiency Paradox: How Next-Gen GPU Architectures Balance Teraflops with Thermal Limits", "ai-gaming", "game-optimization")
    generate_missing("From Code to Canvas: Streamlining the Game Engine Pipeline with Automated AI Asset Generation", "ai-gaming", "game-optimization")
