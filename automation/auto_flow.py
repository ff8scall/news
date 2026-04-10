import time
from trend_collector import TrendCollector
from ai_writer import AIWriter
from datetime import datetime
import subprocess

def run_batch_automation(post_count=3):
    print(f"=== [SEO Blog Automation: Batch Production Mode ({post_count} posts)] ===")
    
    collector = TrendCollector()
    writer = AIWriter()
    
    # 1. 트렌드 수집
    trends = collector.collect_all()
    if not trends:
        print("[!] 트렌드 수집 실패.")
        return False

    success_count = 0
    # 상위 N개 키워드에 대해 순차 작업
    for i in range(min(post_count, len(trends))):
        item = trends[i]
        keyword = item['keyword']
        print(f"\n[*] 작업 시작 ({i+1}/{post_count}): {keyword}")
        
        try:
            # 1분당 할당량을 고려한 지능형 대기 (첫 번째가 아닐 때만 대기)
            if i > 0:
                print(f"[*] 안전 대기 중 (60초... 할당량 보호)")
                time.sleep(60)

            content = writer.generate_content(keyword, item['news_title'])
            if content and len(content) > 500:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"auto_{timestamp}_{i}.md"
                writer.save_post(content, filename)
                print(f"[V] 포스팅 생성 성공: {keyword}")
                success_count += 1
            else:
                print(f"[X] 내용 생성 실패 또는 품질 미달: {keyword}")
        except Exception as e:
            print(f"[!] 에러 발생: {e}")

    # 3. 배포 (성공한 게 하나라도 있다면)
    if success_count > 0:
        print(f"\n[*] {success_count}개 포스팅 생성 완료. GitHub 배포를 시작합니다...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"feat: add {success_count} automated trend posts"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[🚀] 배포 완료!")
            return True
        except Exception as e:
            print(f"[X] 배포 실패: {e}")
            return False
    return False

if __name__ == "__main__":
    # 안전하게 3개만 먼저 대량 수집해 보겠습니다.
    run_batch_automation(post_count=3)
