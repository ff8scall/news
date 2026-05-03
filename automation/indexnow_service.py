import os
import time
import requests
import logging
from dotenv import load_dotenv
from google_indexing_service import notify_google_indexing

load_dotenv()

logger = logging.getLogger("LegoSia.IndexNow")

def notify_indexnow(urls):
    """
    Search engines(Bing, Naver 등)에 새 URL 생성을 알림.
    [V14.8] Batch Mode (POST) 확정: 신규 생성된 기사(Newly Created)의 효율적 색인을 위해 배치 전송 사용.
    """
    if not urls:
        return
    
    # 중복 제거 및 정체
    urls = list(set([u.strip() for u in urls if u.strip()]))
    if not urls: return

    # 호스트 추출 (첫 번째 URL 기준)
    from urllib.parse import urlparse
    parsed_home = urlparse(urls[0])
    host = parsed_home.netloc
    
    bing_key = os.getenv("INDEXNOW_KEY_BING", "bbd0d9a6843c450eb3e9d811a0fd504a")
    naver_key = os.getenv("INDEXNOW_KEY_NAVER", "c3a4f8e21d6b4927a7c5b1e0d3f4a6b2")
    
    targets = [
        {"name": "Bing", "url": "https://www.bing.com/indexnow", "key": bing_key},
        {"name": "Naver", "url": "https://searchadvisor.naver.com/indexnow", "key": naver_key},
        {"name": "Yandex", "url": "https://yandex.com/indexnow", "key": bing_key},
        {"name": "IndexNow.org", "url": "https://api.indexnow.org/indexnow", "key": bing_key}
    ]
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (LegoSiaBot/1.0; +https://news.lego-sia.com)"
    }

    # [V14.8] 다건 전송 시 POST(Batch) 방식을 기본으로 사용
    print(f" [*] Batch notifying {len(urls)} URLs to IndexNow Engines (Newly Created Focus)...")
    
    for target in targets:
        payload = {
            "host": host,
            "key": target["key"],
            "keyLocation": f"https://{host}/{target['key']}.txt",
            "urlList": urls
        }
        try:
            # POST 방식이 색인 성공률과 속도 면에서 신규 기사 대량 등록 시 유리함
            res = requests.post(target["url"], json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 202]:
                logger.info(f" [SUCCESS] {target['name']} Batch: {len(urls)} URLs ({res.status_code})")
                print(f" [OK] {target['name']} batch accepted.")
            else:
                logger.warning(f" [FAIL] {target['name']} Batch: {res.status_code} - {res.text[:100]}")
                print(f" [!] {target['name']} failed: {res.status_code}")
        except Exception as e:
            logger.error(f" [ERROR] {target['name']} Batch Error: {e}")

    # Google Indexing API (신규 기사 실시간 색인 핵심)
    try:
        notify_google_indexing(urls)
    except Exception as e:
        logger.error(f"Google Indexing error: {e}")

if __name__ == "__main__":
    # Test call
    logging.basicConfig(level=logging.INFO)
    test_urls = ["https://news.lego-sia.com/posts/2026/04/test-article/"]
    notify_indexnow(test_urls)

