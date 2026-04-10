import requests
import json

def submit_indexnow(site_url, key):
    """
    IndexNow API를 통해 검색 엔진(Bing, Yandex 등)에 사이트 업데이트 알림을 보냅니다.
    """
    # IndexNow API endpoint (Bing)
    endpoint = "https://www.bing.com/indexnow"
    
    data = {
        "host": site_url.replace("https://", "").replace("/", ""),
        "key": key,
        "keyLocation": f"{site_url}{key}.txt",
        "urlList": [
            site_url,
            f"{site_url}posts/"
        ]
    }
    
    try:
        response = requests.post(endpoint, json=data, headers={"Content-Type": "application/json; charset=utf-8"})
        if response.status_code == 200:
            print(f"[🚀] IndexNow 제출 성공! (Bing)")
        else:
            print(f"[!] IndexNow 제출 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[X] IndexNow 통신 에러: {e}")

if __name__ == "__main__":
    # 테스트용 단독 실행
    submit_indexnow("https://blog.lego-sia.com/", "bd9cab15af0446658b1e7bd00b8120ca")
