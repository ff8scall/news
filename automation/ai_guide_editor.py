import json
import os
import re
import logging
from ai_writer import AIWriter

logger = logging.getLogger("LegoSia.GuideEditor")

GUIDE_JSON_SCHEMA = """
{
    "guide_title": "Technical Documentation Title",
    "guide_summary": "Technical objective and summary (1-sentence)",
    "guide_type": "Framework/Category",
    "difficulty": "Intermediate | Advanced",
    "guide_content": "Technical Markdown content following Phase 1-4 structure",
    "tags": ["cli", "backend", "api"]
}
"""

class GuideEditor:
    """[V6.0] 전문 엔지니어용 기술 가이드 에디터: CLI 및 코드 중심"""
    def __init__(self, model_name=None, writer=None):
        self.model_name = model_name
        self.writer = writer if writer else AIWriter()

    def _extract_json_safe(self, text):
        if not text: return None
        stack = []
        start = -1
        for i, char in enumerate(text):
            if char == '{':
                if start == -1: start = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        try: return json.loads(text[start:i+1], strict=False)
                        except: return None
        return None

    def write_guide(self, news_draft, lang='ko'):
        """[V6.0] 실무자용 심층 기술 문서 집필"""
        summary = news_draft.get('kor_summary', '')
        if isinstance(summary, list): summary = " ".join(summary)
            
        language_name = "Korean" if lang == 'ko' else "English"
        
        prompt = f"""
            [STRICT TECHNICAL DOCUMENTATION PROTOCOL]:
            1. TARGET AUDIENCE: System Engineers and Backend Developers.
            2. TONE & STYLE: 
               - Dry, concise, and professional. 
               - NO emojis, NO greetings, NO flowery language.
               - Use standard Markdown headers (### Phase X).
            3. CONTENT STRUCTURE (MANDATORY):
               - ### Overview: Technical objectives and architecture.
               - ### Phase 1: Infrastructure & Environment Setup
                 - MUST include exact CLI commands (e.g. conda create, pip install).
                 - Specify required CUDA and Python versions.
               - ### Phase 2: Core Implementation & Engine Setup
                 - Specify backend framework (e.g. ComfyUI, FastAPI, Diffusers).
                 - Detailed model weights and loading logic.
               - ### Phase 3: Hardware Tuning & API Integration
                 - VRAM management: Specific params for limited memory (e.g. 12GB).
                 - Provide actual JSON API request/response samples.
               - ### Phase 4: Training & Optimization
                 - LoRA/Fine-tuning params (e.g. 8-bit Adam, Learning Rate).
                 - Requirements for high-end scaling (24GB+).
            4. FORMATTING: Use code blocks (```bash, ```python, ```json) for all technical data.

            [OUTPUT STRUCTURE]: {GUIDE_JSON_SCHEMA}
            [INPUT CONTEXT]:
            - TOPIC: {news_draft.get('kor_title')}
            - OBJECTIVE: {summary}
            - TECHNICAL DATA: {news_draft.get('kor_content', '')}
            """
            
        res = self.writer.generate_content(prompt, model=self.model_name)
        result = self._extract_json_safe(res)
        
        if result and 'guide_content' in result:
            # 보정 로직: 한글 가독성을 위한 최소한의 줄바꿈 (문장 끝 . 뒤에 강제 \n\n)
            # 단, 코드 블록 내부 등은 건드리지 않도록 정교한 처리가 필요하나 
            # 일단 단순 적용 후 테스트하겠습니다.
            content = result['guide_content']
            # 불필요한 이모지 잔재가 생성될 경우 강제 삭제
            content = re.sub(r'[\u1F600-\u1F64F\u1F300-\u1F5FF\u1F680-\u1F6FF\u2600-\u26FF\u2700-\u27BF]', '', content)
            result['guide_content'] = content
            
        return result
