import os
import glob
import re

def super_clean_duplicates():
    paths = glob.glob("content/**/*.md", recursive=True)
    for path in paths:
        with open(path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # 프론트매터 구간 찾기
        fm_indices = [i for i, line in enumerate(lines) if line.strip() == '---']
        if len(fm_indices) < 2: continue
        
        fm_start, fm_end = fm_indices[0], fm_indices[1]
        fm_lines = lines[fm_start:fm_end+1]
        other_lines = lines[fm_end+1:]
        
        new_fm_lines = []
        seen_image = False
        
        # 1. 실제 경로가 있는 image 필드를 우선순위로 정렬
        # (이미지가 두 개 있을 경우 경로가 있는 것을 살림)
        path_image_line = None
        for line in fm_lines:
            if re.search(r'^image:\s*"/images/', line):
                path_image_line = line
                break
        
        # 2. 프론트매터 재구성
        for line in fm_lines:
            if line.startswith('image:'):
                if line == path_image_line and not seen_image:
                    new_fm_lines.append(line)
                    seen_image = True
                else:
                    # 중복이거나 텍스트 프롬프트인 경우 제거
                    continue
            else:
                new_fm_lines.append(line)
        
        # 3. 만약 경로 이미지가 없는데 다른 image(프롬프트) 라인이 있었다면 그것도 제거 (Hugo 에러 방지)
        # 단, 이미지가 아예 없는 경우보다는 하나는 있는 게 좋으므로 일단 중복만 제거하도록 설계
        
        final_content = "".join(new_fm_lines) + "".join(other_lines)
        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write(final_content)
        print(f"Sanitized: {os.path.basename(path)}")

if __name__ == "__main__":
    super_clean_duplicates()
