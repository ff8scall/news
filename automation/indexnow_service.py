import requests
import json
import logging

logger = logging.getLogger("LegoSia.IndexNow")

def notify_indexnow(urls):
    """
    Search engines(Bing, Naver 등)에 새 URL 생성을 알림.
    최적화: keyLocation은 선택 사항이며, 제거 시 Bing이 루트에서 직접 키를 찾도록 유도함.
    """
    if not urls:
        return
    
    host = "news.lego-sia.com"
    key = "bbd0d9a6843c450eb3e9d811a0fd504a"
    
    # 주요 IndexNow 지원 엔드포인트
    endpoints = [
        "https://www.bing.com/indexnow",
        "https://yandex.com/indexnow",
        "https://api.indexnow.org/indexnow" # 통합 엔드포인트
    ]
    
    # [V1.2] 최적화된 페이로드 (keyLocation 제거)
    payload = {
        "host": host,
        "key": key,
        "urlList": urls
    }

    # [V1.2] 강화된 헤더 (User-Agent 추가)
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/123.0.0.0"
    }

    print(f" [*] Sending {len(urls)} URLs to IndexNow (Optimized Payload)...")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    for endpoint in endpoints:
        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f" [SUCCESS] Indexed at {endpoint} (Status: 200)")
            elif res.status_code == 202:
                print(f" [ACCEPTED] {endpoint} accepted the request (Status: 202)")
            else:
                print(f" [!] {endpoint} returned status {res.status_code}")
                print(f" Response: {res.text}")
        except Exception as e:
            print(f" [ERROR] Could not notify {endpoint}: {e}")

if __name__ == "__main__":
    # Test call
    logging.basicConfig(level=logging.INFO)
    test_urls = ["https://news.lego-sia.com/posts/2026/04/test-article/"]
    notify_indexnow(test_urls)

