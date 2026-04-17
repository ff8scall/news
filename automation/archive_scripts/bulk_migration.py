import os
import glob
from ai_writer import AIWriter
from telegram_notifier import TelegramNotifier

class BulkMigrator:
    def __init__(self):
        self.writer = AIWriter()
        self.notifier = TelegramNotifier()

    def run_all(self):
        # 모든 하부 카테고리 기사 전수 수집
        all_posts = glob.glob("content/posts/**/*.md", recursive=True)
        print(f"[*] Bulk Migration: Processing {len(all_posts)} articles...")
        
        success_count = 0
        for post_path in all_posts:
            # 설정 파일 등 제외
            if "_index" in post_path: continue
            
            with open(post_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            print(f"[*] Migrating: {os.path.basename(post_path)}...")
            
            prompt = f"""
            너는 2026년의 시점에서 과거의 기사를 '현대화'하는 마이그레이션 전문가다.
            아래 기사를 2026년 최신 기술 표준과 우리 블로그의 프리미엄 정책에 맞게 수정하라.
            
            [원문 기사]
            {content}
            
            [수정 가이드]
            1. 시점은 2026년이다. (예: NVIDIA Blackwell은 이제 구형이며, 현재는 Rubin 또는 HBM4가 대세다.)
            2. 우리 블로그의 시그니처인 'AI 전문 편집장 3줄 요약'을 본문 상단에 추가하라.
            3. 문체는 차분하고 전문적인 존댓말로 통일하라.
            4. FrontMatter(제목, 태그 등)를 보존하거나 더 세련되게 다듬어라.
            
            오직 수정된 '전체 마크다운 본문'만 응답하라.
            """
            
            revised = self.writer.generate_content(prompt, is_direct_prompt=True)
            if revised:
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(revised.strip())
                success_count += 1
            
        self.notifier.send_message(f"🏗️ **[대규모 마이그레이션 완료]**\n\n- 전체 {len(all_posts)}건 중 {success_count}건 정밀 마이그레이션 성공\n- 모든 과거 기사가 2026년형 프리미엄 버전으로 교체되었습니다. 🛰️")

if __name__ == "__main__":
    migrator = BulkMigrator()
    migrator.run_all()
