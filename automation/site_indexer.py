import requests
import json

def submit_indexnow(site_url, key):
    """
    IndexNow API를 통해 검색 엔진(Bing, Yandex 등)에 사이트 업데이트 알림을 보냅니다.
    최적화: keyLocation은 선택 사항이며, 제거 시 Bing이 루트에서 직접 키를 찾도록 유도함.
    """
    # IndexNow 통합 엔드포인트 또는 Bing 엔드포인트
    endpoint = "https://www.bing.com/indexnow"
    
    # [V1.2] 최적화된 페이로드 (keyLocation 제거)
    data = {
        "host": site_url.replace("https://", "").replace("/", ""),
        "key": key,
        "urlList": [
            site_url,
            f"{site_url}posts/"
        ]
    }
    
    # [V1.2] 강화된 헤더 (User-Agent 추가)
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/123.0.0.0"
    }
    
    try:
        response = requests.post(endpoint, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"[🚀] IndexNow 제출 성공! (Status: 200)")
        elif response.status_code == 202:
            print(f"[🚀] IndexNow 요청 수락됨! (Status: 202)")
        else:
            print(f"[!] IndexNow 제출 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[X] IndexNow 통신 에러: {e}")

if __name__ == "__main__":
    # 테스트용 단독 실행
    submit_indexnow("https://news.lego-sia.com/", "bbd0d9a6843c450eb3e9d811a0fd504a")

