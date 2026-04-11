import time
import subprocess
import sys
import os

def run_engine():
    """뉴스 엔진을 실행하고 결과를 출력"""
    print(f"\n[TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Global Tech Sync...")
    try:
        # news_main.py 실행 (출력을 실시간으로 확인)
        result = subprocess.run([sys.executable, "automation/news_main.py"], check=True)
        print(f"[OK] Sync completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Sync failed with error: {e}")
    except Exception as e:
        print(f"[WARN] Unexpected error: {e}")

def main():
    print("=== LEGO-SIA AUTOMATION SERVICE LAUNCHER (V1.0) ===")
    print("Status: 24/7 Monitoring Enabled (1-hour interval)")
    
    # 첫 실행
    run_engine()
    
    # 60분 간격 무한 루프
    while True:
        print(f"\n[*] Sleeping for 60 minutes... zzz")
        time.sleep(3600) # 3600초 (1시간)
        run_engine()

if __name__ == "__main__":
    main()
