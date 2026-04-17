import os
import time
from ai_writer import AIWriter

# 정예 주제 3선
BEST_TOPICS = [
    ("NVIDIA Blackwell GPU: South Korea's Semiconductor Opportunity or Crisis?", "AI·신기술"),
    ("AI News Flipping Strategy: High-Profit Sales Tactics Revealed", "수익화 전략"),
    ("Autonomous Workforce: AutoGen and the Shocking Reality of Multi-Agent Systems", "AI 에이전트")
]

def rebuild_best_posts():
    writer = AIWriter()
    for topic, cat in BEST_TOPICS:
        print(f"[*] Re-generating high-quality post: {topic}")
        try:
            content = writer.generate_content(keyword=topic, category=cat)
            if content:
                safe_title = topic.lower().replace(" ", "-").replace(":", "").replace("'", "")[:30]
                filename = f"best-{int(time.time())}.md"
                # 카테고리별 폴더에 저장
                cat_folder = {
                    'AI·신기술': 'ai-tech',
                    '수익화 전략': 'profit',
                    'AI 에이전트': 'ai-agents'
                }.get(cat, 'others')
                
                os.makedirs(f"content/posts/{cat_folder}", exist_ok=True)
                writer.save_post(content, f"{cat_folder}/{filename}")
                print(f"[SUCCESS] Saved to {cat_folder}/{filename}")
            
            # 명품을 위해 4분간 쿨링 (API 차단 및 과부하 방지)
            print("[WAIT] Cooling down for 120s...")
            time.sleep(120)
            
        except Exception as e:
            print(f"[FAIL] {topic}: {e}")
            time.sleep(30)

if __name__ == "__main__":
    rebuild_best_posts()
