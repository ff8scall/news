import time
from trend_collector import TrendCollector
from ai_writer import AIWriter
from datetime import datetime
import os
import subprocess

def run_automation_until_success():
    print("=== [SEO Blog Automation: Infinite Retry Mode] ===")
    
    collector = TrendCollector()
    writer = AIWriter()
    
    # 1. 트렌드 수집
    trends = collector.collect_all()
    if not trends:
        print("[!] 트렌드 수집 실패. 다시 시도합니다.")
        return False

    item = trends[0]
    keyword = item['keyword']
    print(f"[*] 목표 키워드: {keyword}")
    
    max_retries = 5
    for attempt in range(max_retries):
        print(f"[*] 시도 {attempt + 1}/{max_retries}...")
        try:
            content = writer.generate_content(keyword, item['news_title'])
            if content and len(content) > 500: # 정상적인 글인지 확인
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"auto_{timestamp}.md"
                writer.save_post(content, filename)
                print(f"[🎉] 성공! 포스팅이 생성되었습니다.")
                return True
        except Exception as e:
            print(f"[!] 실패: {e}")
        
        print("[*] 45초 휴식 후 다음 모델/API로 재시도합니다...")
        time.sleep(45)
        
    return False

if __name__ == "__main__":
    success = run_automation_until_success()
    if success:
        print("[*] 생성 성공. 자가 배포(Git Push)를 시작합니다.")
        # Git Push 자동화
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "chore: automatic post generation"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[🚀] 배포 완료! 라이브 사이트에서 확인하세요.")
        except Exception as e:
            print(f"[X] 배포 실패: {e}")
