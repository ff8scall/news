import os
import re
import shutil

others_dir = 'content/posts/others'
target_base = 'content/posts'
categories_map = {
    'AI·신기술': 'ai-tech',
    'AI 에이전트': 'ai-agents',
    '수익화 전략': 'profit',
    '캠핑': 'camping'
}

if not os.path.exists(others_dir):
    print("No others directory found.")
    exit()

files = os.listdir(others_dir)
for f in files:
    src = os.path.join(others_dir, f)
    try:
        with open(src, 'r', encoding='utf-8') as file:
            content = file.read()
            match = re.search(r'categories:\s*\[\"(.*)\"\]', content)
            if match:
                cat_name = match.group(1).strip()
                # 캠핑 관련은 모두 camping 폴더로
                folder = 'camping' if '캠핑' in cat_name else categories_map.get(cat_name, 'others')
                
                if folder == 'others':
                    continue
                
                dest_dir = os.path.join(target_base, folder)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                shutil.move(src, os.path.join(dest_dir, f))
                print(f"Success: {f} -> {folder}/")
    except Exception as e:
        print(f"Error {f}: {e}")

# 다 옮겼으면 others 폴더 삭제 시도 (비어있을 경우)
try:
    if not os.listdir(others_dir):
        os.rmdir(others_dir)
        print("Cleaned up others folder.")
except:
    pass

print("Final cleanup done.")
