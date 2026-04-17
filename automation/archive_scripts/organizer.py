import os
import re
import shutil

posts_dir = 'content/posts'
categories_map = {
    'AI·신기술': 'ai-tech',
    'AI 에이전트': 'ai-agents',
    '수익화 전략': 'profit',
    '캠핑': 'camping',
    '캠핑트렌드': 'camping',
    '캠핑육아': 'camping',
    '캠핑안전': 'camping',
    '펫캠핑': 'camping',
    '캠핑요리': 'camping'
}

# 대상 마크다운 파일 리스트 (서브폴더에 이미 들어간 건 제외)
files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]

for f in files:
    filepath = os.path.join(posts_dir, f)
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            # 프런트매터에서 카테고리 추출
            cat_match = re.search(r'categories:\s*\[\"(.*)\"\]', content)
            if cat_match:
                cat_name = cat_match.group(1).strip()
                target_folder = categories_map.get(cat_name, 'others')
                
                target_path = os.path.join(posts_dir, target_folder)
                if not os.path.exists(target_path):
                    os.makedirs(target_path)
                
                # 파일 이동
                shutil.move(filepath, os.path.join(target_path, f))
                print(f"[OK] Moved {f} to {target_folder}/")
            else:
                print(f"[!] No category found in {f}")
    except Exception as e:
        print(f"[!] Error processing {f}: {e}")

print("\n=== 폴더 정리 완료 ===")
