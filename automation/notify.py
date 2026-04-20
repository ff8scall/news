import sys
import os
from telegram_bridge import TelegramBridge

def main():
    bridge = TelegramBridge()
    
    # 인자가 있으면 해당 내용을 보내고, 없으면 기본 완료 메시지 전송
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = "✅ [Antigravity] 요청하신 모든 작업이 완료되었습니다."
        
    if bridge.send_report(message):
        print(f"Notification sent successfully.")
    else:
        print("Failed to send notification.")

if __name__ == "__main__":
    main()
