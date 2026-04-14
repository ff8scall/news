import os
import glob
import re

def fix_duplicate_keys():
    paths = glob.glob("content/**/*.md", recursive=True)
    for path in paths:
        with open(path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        new_lines = []
        image_url = None
        has_image_prompt = False
        
        # 1. 이미지 관련 데이터 수집 및 중복 라인 제거
        for line in lines:
            # 이미지 URL이 담긴 라인 탐지
            if 'image: "/images/posts/' in line:
                match = re.search(r'image:\s*"(.*?)"', line)
                if match: image_url = match.group(1)
                continue
            # AI 프롬프트 라인 탐지
            if 'image_prompt_core:' in line or ('image:' in line and not '/images/posts/' in line):
                has_image_prompt = True
                continue
            new_lines.append(line)
        
        # 2. 하나의 깨끗한 image 필드로 통합하여 주입
        if image_url:
            # description 뒤에 주입
            final_lines = []
            for line in new_lines:
                final_lines.append(line)
                if 'description:' in line:
                    final_lines.append(f'image: "{image_url}"\n')
            
            with open(path, 'w', encoding='utf-8-sig') as f:
                f.writelines(final_lines)
            print(f"Repaired: {os.path.basename(path)}")

if __name__ == "__main__":
    fix_duplicate_keys()
