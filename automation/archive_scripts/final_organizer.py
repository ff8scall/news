import os
import re
import shutil
import time

posts_dir = 'content/posts'
categories_map = {
    'AI·신기술': 'ai-tech',
    'AI 에이전트': 'ai-agents',
    '수익화 전략': 'profit',
    '캠핑': 'camping'
}

# 1. 파일 핸들을 놓아줄 때까지 아주 잠시 대기
time.sleep(1)

files = [f for f in os.listdir(posts_dir) if f.endswith('.md')]

for f in files:
    src = os.path.join(posts_dir, f)
    try:
        with open(src, 'r', encoding='utf-8') as file:
            content = file.read()
            match = re.search(r'categories:\s*\[\"(.*)\"\]', content)
            if match:
                cat_name = match.group(1).strip()
                # '캠핑' 포함 모든 캠핑류 통합
                folder = 'camping' if '캠핑' in cat_name else categories_map.get(cat_name, 'others')
                dest_dir = os.path.join(posts_dir, folder)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                dest = os.path.join(dest_dir, f)
                # 이동 시도 (실패 시 복사 후 삭제)
                try:
                    shutil.move(src, dest)
                    print(f"Moved: {f} -> {folder}")
                except:
                    shutil.copy2(src, dest)
                    os.remove(src)
                    print(f"Copied & Deleted: {f} -> {folder}")
    except Exception as e:
        print(f"Error {f}: {e}")

print("Done.")
