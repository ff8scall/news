import os
import time
import requests
import subprocess
from dotenv import load_dotenv

# .env 로드
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

class TelegramRemote:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.last_update_id = 0

    def send_resp(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"})

    def handle_command(self, cmd):
        if cmd == "/news":
            self.send_resp("🛰️ **뉴스 수집 명령 수신!** 인공지능 편집장을 깨우고 있습니다. 잠시만 기다려주세요...")
            # news_main.py 실행
            subprocess.run(["python", "automation/news_main.py"])
        
        elif cmd == "/status":
            # 전체 포스트 개수 확인
            post_count = 0
            for root, dirs, files in os.walk("content/posts"):
                post_count += len([f for f in files if f.endswith(".md")])
            self.send_resp(f"📊 **Lego-sia 블로그 현황**\n\n- 전체 정예 기사: {post_count}개\n- 시스템 상태: 정상 운영 중 ✅")
            
        elif cmd == "/deploy":
            self.send_resp("🚀 **배포 명령 수신!** 사이트를 빌드하고 Netlify로 전송합니다...")
            # 휴고 빌드 및 푸시 (간략화된 예시)
            subprocess.run(["C:\\hugo_tmp\\hugo.exe", "--gc", "--cleanDestinationDir"])
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", "Remote Deploy via Telegram"])
            subprocess.run(["git", "push", "origin", "main"])
            self.send_resp("✨ **배포 완료!** 1~2분 내로 라이브 사이트에 반영됩니다.")
            
        else:
            self.send_resp("❓ 알 수 없는 명령입니다. `/news`, `/deploy`, `/status` 중 하나를 입력해 주세요!")

    def listen(self):
        print("[*] Telegram Remote Receiver Started...")
        self.send_resp("🎮 **Lego-sia 리모컨이 활성화되었습니다.** 이제 명령을 내리실 수 있습니다!")
        
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={self.last_update_id + 1}&timeout=30"
                res = requests.get(url, timeout=40).json()
                
                for update in res.get("result", []):
                    self.last_update_id = update["update_id"]
                    if "message" in update and str(update["message"]["chat"]["id"]) == self.chat_id:
                        text = update["message"].get("text", "")
                        print(f"[*] Received command: {text}")
                        self.handle_command(text)
                        
            except Exception as e:
                print(f"[ERROR] Remote listener error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    remote = TelegramRemote()
    remote.listen()
