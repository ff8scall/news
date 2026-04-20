import os
import requests
from dotenv import load_dotenv

# 환경 변수 로드
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

class TelegramBridge:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_report(self, message):
        """작업 완료 리포트를 전송합니다. (송신 전용)"""
        if not self.token or not self.chat_id:
            return False
        
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            # 텔레그램 메시지 길이 제한(4096자) 대응
            if len(message) > 4000:
                chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                for chunk in chunks:
                    requests.post(url, json={"chat_id": self.chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=10)
            else:
                requests.post(url, json=payload, timeout=10)
            return True
        except Exception as e:
            print(f"Error sending report: {e}")
            return False

if __name__ == "__main__":
    import sys
    bridge = TelegramBridge()
    msg = sys.argv[1] if len(sys.argv) > 1 else "작업이 완료되었습니다. 🚀"
    bridge.send_report(msg)
