import os
import glob
from ai_writer import AIWriter
from telegram_notifier import TelegramNotifier

class FinalGatekeeper:
    def __init__(self):
        self.writer = AIWriter()
        self.notifier = TelegramNotifier()

    def audit_and_migrate(self):
        """방금 작성된 '도장 없는' 새 기사만 골라내어 초스피드 검사"""
        new_posts = glob.glob("content/posts/news/*.md")
        if not new_posts: return
        
        # 아직 검증 전인(verified: true 가 없는) 파일만 필터링
        audit_list = []
        for p in new_posts:
            with open(p, "r", encoding="utf-8") as f:
                if "verified: true" not in f.read():
                    audit_list.append(p)

        if not audit_list: return
        
        print(f"[*] Gatekeeper: Auditing {len(audit_list)} brand-new articles...")
        
        for post_path in audit_list:
            with open(post_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            audit_prompt = f"""
            너는 프리미엄 매거진 편집국장이다. 아래 기사 초안을 검수하라.
            
            [기사 내용]
            {content}
            
            추가 지시: 
            1. FrontMatter에 반드시 'verified: true' 필드를 추가하라.
            2. 품질이 낮으면 'REJECT'라고 말하라.
            
            오직 수정된 '전체 마크다운 본문'만 응답하라.
            """
            
            revised_content = self.writer.generate_content(audit_prompt, is_direct_prompt=True)
            
            if revised_content and "REJECT" not in revised_content:
                # 수정본으로 덮어쓰기 (인증 도장 포함)
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(revised_content.strip())
                print(f"[PASSED] Verified: {os.path.basename(post_path)}")
            else:
                os.remove(post_path)

if __name__ == "__main__":
    gk = FinalGatekeeper()
    gk.audit_and_migrate()
