import os
import glob
import re

def aggressive_fix():
    paths = glob.glob("content/**/*.md", recursive=True)
    for path in paths:
        with open(path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # 1. 기존 이미지 필드 전부 제거
        clean_lines = []
        target_image_path = None
        
        for line in lines:
            # 경로가 포함된 이미지 라인을 찾으면 기억해둠
            if 'image: "/images/posts/' in line:
                match = re.search(r'image:\s*"(.*?)"', line)
                if match: target_image_path = match.group(1)
                continue
            
            # 그 외 모든 이미지 관련 필드 삭제
            if line.startswith('image:') or line.startswith('image_prompt_core:'):
                continue
            
            clean_lines.append(line)
        
        # 2. 이미지 경로가 확인되었다면 description 뒤에 단 하나만 삽입
        if target_image_path:
            final_lines = []
            inserted = False
            for line in clean_lines:
                final_lines.append(line)
                if 'description:' in line and not inserted:
                    final_lines.append(f'image: "{target_image_path}"\n')
                    inserted = True
            
            with open(path, 'w', encoding='utf-8-sig') as f:
                f.writelines(final_lines)
            print(f"Aggressively Repaired: {os.path.basename(path)}")
        else:
            # 이미지가 없던 파일은 그대로 보존 (혹은 images 필드 잔재 제거)
            with open(path, 'w', encoding='utf-8-sig') as f:
                f.writelines(clean_lines)

if __name__ == "__main__":
    aggressive_fix()
