import os
import time
import requests
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# [V3.3] 멀티태스킹 패치: 비동기 실행으로 명령 응답 지연 해소
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

class TelegramRemote:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.last_update_id = 0
        self.last_run_hour = -1

    def send_resp(self, text):
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            requests.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}, timeout=12)
        except Exception as e:
            print(f"[!] Send Error: {e}")

    def handle_command(self, cmd):
        print(f"[*] Command: {cmd}")
        # Popen을 사용하여 명령을 백그라운드에서 실행 (봇이 멈추지 않음)
        if cmd == "/news":
            self.send_resp("[INFO] Starting news harvest. I'll remain responsive during processing.")
            subprocess.Popen(["python", "automation/news_main.py"])
        
        elif cmd == "/night":
            self.send_resp("[INFO] Starting Night-Mode mass harvest.")
            subprocess.Popen(["python", "automation/news_main.py", "--night"])

        elif cmd == "/status":
            post_count = 0
            # content 하위의 모든 마크다운 파일 카운트 (ko/en 통합)
            for root, dirs, files in os.walk(os.getcwd()):
                if "content" in root:
                    for file in files:
                        if file.endswith(".md") and "_index" not in file:
                            post_count += 1
            self.send_resp(f"[STATUS] Lego-Sia Blog Status\n- Total Articles: {post_count}\n- System: Multi-tasking engine active [OK]")
            
        elif cmd == "/deploy":
            self.send_resp("[DEPLOY] Starting manual deployment.")
            # 배포 명령도 비동기로 실행하여 봇의 응답성을 유지
            deploy_cmd = "hugo --gc --cleanDestinationDir; git add .; git commit -m 'Remote Deploy'; git push origin main"
            subprocess.Popen(f"powershell -Command \"{deploy_cmd}\"", shell=True)

    def listen(self):
        print(f"[*] Multi-tasking Bot Active.")
        self.send_resp("[SYSTEM] Multi-tasking engine upgraded. Ready for commands.")
        
        while True:
            # 자동 스케줄러
            now = datetime.now()
            if now.hour in [1, 2, 3, 4, 5, 6] and now.hour != self.last_run_hour:
                subprocess.Popen(["python", "automation/news_main.py", "--night"])
                self.last_run_hour = now.hour

            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={self.last_update_id + 1}&timeout=30"
                res = requests.get(url, timeout=35).json()
                for update in res.get("result", []):
                    self.last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    if text.startswith("/"):
                        self.handle_command(text)
            except:
                time.sleep(5)

if __name__ == "__main__":
    bot = TelegramRemote()
    bot.listen()
