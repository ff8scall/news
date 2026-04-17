import os
import time
from ai_writer import AIWriter
from dotenv import load_dotenv

load_dotenv()

def audit_v44():
    writer = AIWriter()
    print("=== [Lego-Sia V4.4 ULTIMATE API AUDIT] ===")
    
    targets = [
        ("gemini-pro-latest", "Google Gemini"),
        ("llama-3.3-70b-versatile", "Groq Llama 3.3"),
        ("deepseek-chat", "DeepSeek"),
        ("minimax/minimax-m2.5:free", "OpenRouter Minimax"),
        ("gpt-4o-mini", "GitHub Models"),
        ("@cf/meta/llama-3.1-8b-instruct", "Cloudflare AI")
    ]
    
    for model, label in targets:
        print(f"\n[*] Testing {label} ({model})...")
        try:
            # Note: generate_content now has a 15s wait built-in
            res = writer.generate_content("Say 'OK' and the model name in 5 words.", model=model)
            if res:
                print(f"SUCCESS -> {res.strip()}")
            else:
                print(f"FAILED -> No response")
        except Exception as e:
            print(f"ERROR -> {e}")

if __name__ == "__main__":
    audit_v44()
