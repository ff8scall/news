import os
import re

def patch():
    # 1. amd-and-samsung fix
    p1 = 'content/ko/posts/2026/04/13/amd-and-samsung-forge-strategic-partnership-for-ne-40d6eb.md'
    if os.path.exists(p1):
        with open(p1, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        content = re.sub(r'clusters:.*', 'clusters: ["gpu-hardware"]', content)
        with open(p1, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        print("Fixed Samsung-AMD cluster.")

    # 2. byd-denza fix
    p2 = 'content/ko/posts/2026/04/13/analysis-of-byd-denza-z9-gt-balancing-revolutionar-104eaa.md'
    if os.path.exists(p2):
        with open(p2, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        content = re.sub(r'clusters:.*', 'clusters: ["guides"]', content)
        with open(p2, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        print("Fixed BYD Denza cluster.")

if __name__ == "__main__":
    patch()
