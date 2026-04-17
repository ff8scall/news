import os
import frontmatter
import datetime
from ai_writer import AIWriter

class TrendOutlookGenerator:
    def __init__(self, writer=None):
        self.writer = writer if writer else AIWriter()

    def generate_monthly_report(self, year=None, month=None):
        """특정 월의 기사들을 분석하여 월간 전략 리포트 생성"""
        now = datetime.datetime.now()
        year = year or now.strftime('%Y')
        month = month or now.strftime('%m')
        
        base_path = f"content/ko/posts/{year}/{month}"
        if not os.path.exists(base_path):
            print(f" [!] No posts found for {year}/{month}")
            return None

        # 1. 해당 월의 모든 기사 요약 수집
        print(f" [*] Collecting data for {year}-{month} Outlook...")
        corpus = []
        for file in os.listdir(base_path):
            if file.endswith(".md"):
                post = frontmatter.load(os.path.join(base_path, file))
                corpus.append(f"- 제목: {post.get('title')}\n  요약: {post.get('description')}")

        if len(corpus) < 5:
            print(" [!] Too few posts to generate a meaningful report.")
            return None

        # 2. AI에게 전략적 리포트 생성 요청
        prompt = f"""
        Identity: Top-tier Tech Strategy Consultant.
        Task: Synthesize the following {len(corpus)} tech articles from {year}년 {month}월 into a "Monthly Strategic Outlook".
        Structure:
        1. Executive Summary (Overview of the month)
        2. Top 3 Strategic Pillars (Clustered trends)
        3. Market Outlook (Predictions for the next month)
        4. Competitive Landscape Analysis
        
        Rules: Professional Korean business tone, sharp insights, high-end formatting.
        
        Data Corpus:
        {chr(10).join(corpus)}
        """
        
        print(" [*] Generating Strategic Outlook via AI (High-tier model)...")
        report_content = self.writer.generate_content(prompt, model="gemini-2.0-flash")
        
        if report_content:
            # 3. 리포트 파일로 저장
            filename = f"strategic-outlook-{year}-{month}.md"
            save_path = f"content/ko/posts/{year}/{month}/{filename}"
            
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("---\n")
                f.write(f"title: \"Strategic Outlook {year}-{month}: 테크 트렌드 심층 전망\"\n")
                f.write(f"date: \"{now.strftime('%Y-%m-%dT%H:%M:%S+09:00')}\"\n")
                f.write(f"description: \"{year}년 {month}월의 테크 지형도를 분석하고 다음 달의 핵심 비즈니스 임팩트를 예측합니다.\"\n")
                f.write("categories: [\"tech-biz\"]\n")
                f.write("featured: true\n")
                f.write("---\n\n")
                f.write(report_content)
            
            print(f" [OK] Monthly Strategic Outlook generated: {save_path}")
            return save_path
        return None

if __name__ == "__main__":
    gen = TrendOutlookGenerator()
    gen.generate_monthly_report()
