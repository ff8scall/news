import os
import glob
from ai_writer import AIWriter
from telegram_notifier import TelegramNotifier

class FinalGatekeeper:
    def __init__(self):
        self.writer = AIWriter()
        self.notifier = TelegramNotifier()

    def audit_and_migrate(self):
        """배포 전 content/posts/news 폴더의 모든 신규 기사 전수 검사"""
        new_posts = glob.glob("content/posts/news/*.md")
        if not new_posts: return
        
        print(f"[*] Final Gatekeeper: Auditing {len(new_posts)} new articles...")
        
        for post_path in new_posts:
            with open(post_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 제미나이에게 최종 검역 위임 (마이그레이션 및 SEO 교정)
            audit_prompt = f"""
            너는 세계 최고의 프리미엄 기술 매거진의 편집국장이다. 
            아래 기사는 현재 우리 블로그에 등록될 대기 중인 초안이다.
            
            [기사 내용]
            {content}
            
            [미션]
            1. 이 기사가 2026년 최신 기술 트렌드(NVIDIA Rubin, GPT-6 등)에 부합하는지 확인하라. (구형 정보면 과감히 삭제 대상임을 알릴 것)
            2. 우리 블로그의 2단계 계층 구조와 프리미엄 문체(정중한 존댓말 3줄 요약)가 잘 지켜졌는지 확인하고 교정하라.
            3. Hugo의 FrontMatter 양식(Title, Categories, Tags)이 깨지지 않았는지 확인하라.
            
            오직 수정된 '전체 마크다운 본문'만 응답하라. 만약 기사 품질이 너무 낮아 버려야 한다면 'REJECT'라고 써라.
            """
            
            revised_content = self.writer.generate_content(audit_prompt, is_direct_prompt=True)
            
            if revised_content and "REJECT" not in revised_content:
                # 수정본으로 덮어쓰기 (마이그레이션 완료)
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(revised_content.strip())
                print(f"[PASSED] {os.path.basename(post_path)} has been verified.")
            else:
                # 폐기
                os.remove(post_path)
                print(f"[REJECTED] {os.path.basename(post_path)} failed final verification and was deleted.")

if __name__ == "__main__":
    gk = FinalGatekeeper()
    gk.audit_and_migrate()
