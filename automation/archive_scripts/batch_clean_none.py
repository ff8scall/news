import os
import re

def clean_none_sections(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    
    # 패턴: ## 헤더 \n (개행) None  (개행 또는 다음 헤더 혹은 파일 끝)
    # 정규식: ## 로 시작하는 헤더부터 그 다음 내용이 None/N/A 인 경우까지 한꺼번에 매칭
    new_content = re.sub(r'##.*?\n+(None|N/A|참고 사항 없음|준비 중)\s*(?=\n#|$)', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # 중복 개행 정리
    new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip() + "\n"
    
    if content != new_content:
        with open(file_path, "w", encoding="utf-8-sig") as f:
            f.write(new_content)
        return True
    return False

def main():
    base_paths = [
        "content/en/posts/2026/04/13",
        "content/ko/posts/2026/04/13"
    ]
    
    count = 0
    for base_path in base_paths:
        if not os.path.exists(base_path): continue
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".md"):
                    if clean_none_sections(os.path.join(root, file)):
                        count += 1
                        print(f"[세정 완료] {file}")

    print(f"\n--- 총 {count}개의 파일에서 빈 섹션을 제거했습니다. ---")

if __name__ == "__main__":
    main()
