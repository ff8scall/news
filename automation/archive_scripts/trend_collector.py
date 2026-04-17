import feedparser
import requests
import json
from datetime import datetime

class TrendCollector:
    """실시간 트렌드 및 뉴스 키워드를 수집하는 클래스"""
    
    def __init__(self):
        # 가장 안정적인 구글 뉴스 RSS 활용
        self.sources = {
            "google_news": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        }

    def fetch_rss(self, url):
        try:
            feed = feedparser.parse(url)
            results = []
            for entry in feed.entries:
                results.append({
                    "keyword": entry.title,
                    "news_title": entry.get("summary", ""),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
            return results
        except Exception as e:
            print(f"[!] RSS 에러: {e}")
            return []

    def collect_all(self):
        print("[*] 구글 뉴스 기반 트렌드 수집 중...")
        all_trends = self.fetch_rss(self.sources["google_news"])
        
        # 필터링: 제목이 너무 짧거나 이상한 것 제외
        valid_trends = [t for t in all_trends if len(t['keyword']) > 5]
        return valid_trends[:10]

if __name__ == "__main__":
    collector = TrendCollector()
    hot_topics = collector.collect_all()
    print(f"[*] {len(hot_topics)}개의 키워드를 수집했습니다.")
    for t in hot_topics[:5]:
        print(f"- {t['keyword']}")
