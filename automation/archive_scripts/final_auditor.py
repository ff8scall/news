import os
import re

def audit_relevancy():
    posts_dir = "content/posts"
    deleted_count = 0
    
    # 2026년 기준 2년 이상 지난 구형 키워드 혹은 정보
    # 이 녀석들이 '최신'이나 '기회' 같은 단어와 결합되면 삭제
    outdated_keywords = [
        "Blackwell", "블랙웰", "GPT-4", "Llama 3", "Midjourney v6", 
        "iPhone 15", "Galaxy S24", "Apple Vision Pro (1st)"
    ]

    print("[*] Starting 2026 Relevancy Audit...")

    for root, dirs, files in os.walk(posts_dir):
        for file in files:
            if not file.endswith(".md"): continue
            path = os.path.join(root, file)
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    # 제목 추출
                    match = re.search(r'title:\s*"(.*?)"', content)
                    if not match: continue
                    title = match.group(1)
                    
                    # 검열 필터
                    should_delete = False
                    if any(kw.lower() in title.lower() for kw in outdated_keywords):
                        # 만약 제목에 2년 전 구형 키워드가 있다면 과감히 정리
                        # 단, '역사'나 '회고' 같은 글은 살릴 수 있지만 현재는 매거진 성격상 과감히 쳐냅니다.
                        should_delete = True

                    if should_delete:
                        print(f"[OUTDATED] Removing: {title}")
                        os.remove(path)
                        deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Could not audit {path}: {e}")

    print(f"\n[FINISH] Auditor removed {deleted_count} outdated articles.")
    print("[*] Re-run Hugo build & deploy to reflect 100% fresh 2026 content.")

if __name__ == "__main__":
    audit_relevancy()
