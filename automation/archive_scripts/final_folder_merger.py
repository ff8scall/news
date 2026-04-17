import os
import shutil

content_dir = 'content'
posts_dir = os.path.join(content_dir, 'posts')
os.makedirs(posts_dir, exist_ok=True)

# 이동 규칙 (폴더명: 타겟폴더명)
MAPPING = {
    'it': 'ai-tech',
    'ai-tech': 'ai-tech',
    'ai-agents': 'ai-agents',
    'profit': 'profit',
    'camping': 'camping',
    'cooking': 'camping',
    'lifestyle': 'camping',
    'others': 'others'
}

# 1. content 하부 모든 폴더 순회 (posts는 제외)
for folder in os.listdir(content_dir):
    src_path = os.path.join(content_dir, folder)
    if not os.path.isdir(src_path) or folder == 'posts':
        continue
    
    target_folder_name = MAPPING.get(folder, 'others')
    dest_path = os.path.join(posts_dir, target_folder_name)
    
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    # 원본 폴더 내부 모든 파일 이동
    for f in os.listdir(src_path):
        f_src = os.path.join(src_path, f)
        f_dest = os.path.join(dest_path, f)
        if os.path.isfile(f_src):
            try:
                # 덮어쓰기 방지 (파일명 겹칠 경우 이름 변경)
                if os.path.exists(f_dest):
                    f_dest = f_dest.replace(".md", "_1.md")
                shutil.move(f_src, f_dest)
                print(f"Moved: {folder}/{f} -> posts/{target_folder_name}/")
            except Exception as e:
                print(f"Error moving {f}: {e}")

    # 원본 폴더 삭제 (성공하든 말든 시도)
    try:
        shutil.rmtree(src_path)
    except:
        pass

print("Final merger complete.")
