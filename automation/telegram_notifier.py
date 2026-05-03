import os
import requests
from dotenv import load_dotenv

# .env 로드 (프로젝트 루트 참조)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

class TelegramNotifier:
    def __init__(self):
        # 사용자님이 주신 토큰을 .env에 저장할 예정입니다.
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_message(self, text="[Lego-sia] 작업완료 🚀"):
        if not self.token or not self.chat_id:
            print("[!] Telegram Token or Chat ID missing.")
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print("[SUCCESS] Telegram notification sent.")
                return True
            else:
                print(f"[ERROR] Telegram failed: {res.text}")
                return False
        except Exception as e:
            print(f"[ERROR] Telegram exception: {e}")
            return False

if __name__ == "__main__":
    notifier = TelegramNotifier()
    notifier.send_message("테스트: Lego-sia 블로그 무인 시스템 가동 중! 🛰️")
