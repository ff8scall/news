import json
import os
import time
import requests
import logging
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# [V4.6] Resilient Multi-Engine Orchestrator: Pure Free-Tier (DeepSeek Excluded)
# [FIX] Removed DeepSeek-Chat to avoid potential paid-tier requirements.
# [FEATURE] Unified 15s Request Throttling remains active.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LegoSia.AIWriter")

class AIWriter:
    """[V4.5] 순수 무료 지능 엔진: Gemini, Groq (Llama 3.3), OpenRouter, GitHub, Cloudflare 전용"""
    def __init__(self):
        load_dotenv()
        
        # 1. API 클라이언트 및 토큰 설정
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                logger.info("Gemini V2 SDK Client Activated (Free Tier).")
            except Exception as e: logger.error(f"Gemini Init Fail: {e}")

        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.cf_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.cf_token = os.getenv("CLOUDFLARE_API_TOKEN")

        # [V4.6] 초고성능(Ultra) 모델 풀 (Gemma 4급 - 순수 무료)
        self.ultra_online_models = [
            "gemini-pro-latest",                # Google (V2 SDK 'latest' 선호)
            "llama-3.3-70b-versatile",          # Groq (초고속/초고성능)
            "minimax/minimax-m2.5:free",        # OpenRouter (정교한 한국어)
            "google/gemma-4-31b-it:free",       # OpenRouter (Gemma 4 대안)
            "gpt-4o"                            # GitHub
        ]
        
        # [V4.6] 효율성(Fast) 모델 풀 (신속 처리)
        self.fast_online_models = [
            "gemini-flash-latest",
            "llama-3.1-8b-instant",             # Groq
            "gpt-4o-mini",                     # GitHub
            "@cf/meta/llama-3.1-8b-instruct"    # Cloudflare
        ]

        # [V5.0] 필터링 전용 경량 모델 (RPD: 1000, RPM: 15)
        self.filter_models = [
            "gemini-2.5-flash-lite",               # 최신 고효율 라이트 모델
            "gemini-2.0-flash-lite",               # 안정적인 폴백
            "gemini-1.5-flash",                    # 검증된 범용 모델 (latest 대신 정식 명칭 사용)
            "gemini-1.5-pro"                       # 최후의 수단
        ]

        logger.info("AIWriter V4.5 (Pure Free Master) Activated.")

    def _wait_for_quota(self, seconds=15):
        """[V4.5] 모든 요청 시 15초 휴식 룰 적용"""
        logger.info(f"Throttling: Waiting {seconds}s for safe API quota usage...")
        time.sleep(seconds)

    def _call_gemini_api(self, prompt, model):
        if not self.gemini_client: return None
        try:
            response = self.gemini_client.models.generate_content(
                model=model, contents=prompt,
                config={'max_output_tokens': 8192, 'temperature': 0.7}
            )
            if response and response.text: return response.text
        except Exception as e: logger.warning(f"Gemini API Error ({model}): {e}")
        return None

    def _call_groq_api(self, prompt, model):
        if not self.groq_key: return None
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
            data = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
            res = requests.post(url, headers=headers, json=data, timeout=30)
            if res.status_code == 200: return res.json()['choices'][0]['message']['content']
        except Exception as e: logger.warning(f"Groq API Error ({model}): {e}")
        return None

    def _call_openrouter_api(self, prompt, model):
        if not self.openrouter_key: return None
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json"}
            data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
            res = requests.post(url, headers=headers, json=data, timeout=60)
            if res.status_code == 200: return res.json()['choices'][0]['message']['content']
        except Exception as e: logger.warning(f"OpenRouter API Error ({model}): {e}")
        return None

    def _call_cloudflare_api(self, prompt, model="@cf/meta/llama-3.1-8b-instruct"):
        if not self.cf_account_id or not self.cf_token: return None
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/run/{model}"
            headers = {"Authorization": f"Bearer {self.cf_token}"}
            data = {"messages": [{"role": "user", "content": prompt}]}
            res = requests.post(url, headers=headers, json=data, timeout=60)
            if res.status_code == 200: return res.json()['result']['response']
        except Exception as e: logger.warning(f"Cloudflare AI Error: {e}")
        return None

    def _call_github_api(self, prompt, model):
        if not self.github_token: return None
        endpoint = "https://models.github.ai/inference/chat/completions"
        headers = {"Authorization": f"Bearer {self.github_token}", "Content-Type": "application/json", "X-GitHub-Api-Version": "2026-03-10"}
        payload = {"model": model if model else "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            if response.status_code == 200: return response.json()['choices'][0]['message']['content']
        except Exception as e: logger.warning(f"GitHub API Error: {e}")
        return None

    def _call_ollama_api(self, prompt, model="qwen2.5-coder:14b"):
        """[V4.6] Local Inference: Ollama (localhost:11434)"""
        try:
            url = "http://100.112.163.11:11434/api/generate"
            payload = {"model": model, "prompt": prompt, "stream": False}
            res = requests.post(url, json=payload, timeout=900) # Local can be very slow for 26B+ models
            if res.status_code == 200:
                return res.json().get('response')
        except Exception as e:
            logger.warning(f"Ollama API Error ({model}): {e}")
        return None

    def generate_content(self, prompt, model=None, role=None):
        # 1. 모델이 'gemma4'나 'local'로 시작하면 로컬 Ollama 호출
        if model and (model.startswith("qwen") or "local" in model.lower()):
             return self._call_ollama_api(prompt, model if ":" in model else "qwen2.5-coder:14b")

        # 15초 휴식 룰 (V4.5) - 로컬 요청 시에는 휴식 제외할 수도 있으나 일관성을 위해 유지하거나 로컬일때만 스킵 가능
        # 여기서는 클라우드 API 호출 시에만 휴식하도록 조정
        if not (model and (model.startswith("qwen") or "local" in model.lower())):
            self._wait_for_quota(15)

        # 2. 특정 모델 지정 시
        if model:
            if "gemini" in model.lower(): return self._call_gemini_api(prompt, model)
            if "cf/" in model.lower(): return self._call_cloudflare_api(prompt, model)
            if "llama" in model.lower(): return self._call_groq_api(prompt, model)
            if "google/" in model.lower() or "minimax/" in model.lower(): return self._call_openrouter_api(prompt, model)
            if "gpt-4o" in model.lower(): return self._call_github_api(prompt, model)

        # 3. 역할별 전략적 풀 가동 (Ultra)
        if role in ['writing', 'analysis']:
            for m in self.ultra_online_models:
                res = None
                if "gemini" in m: res = self._call_gemini_api(prompt, m)
                elif "llama" in m: res = self._call_groq_api(prompt, m)
                elif "gpt-4o" in m: res = self._call_github_api(prompt, m)
                else: res = self._call_openrouter_api(prompt, m)
                if res: return res
        
        # 4. 역할별 전략적 풀 가동 (Fast)
        else:
            for m in self.fast_online_models:
                res = None
                if "gemini" in m: res = self._call_gemini_api(prompt, m)
                elif "llama" in m and "cf/" not in m: res = self._call_groq_api(prompt, m)
                elif "cf/" in m: res = self._call_cloudflare_api(prompt, m)
                else: res = self._call_github_api(prompt, m)
                if res: return res
            
        return self._call_openrouter_api(prompt, "minimax/minimax-m2.5:free")

    def score_articles(self, prompt):
        """[V5.0] 필터링 전용: 15초 쓰로틀링 유지하며 빠른 경량 모델 호출"""
        for model in self.filter_models:
            # 필터링도 동일하게 15초 대기 룰 적용 (사용자 요청)
            self._wait_for_quota(15)
            result = self._call_gemini_api(prompt, model)
            if result:
                return result
        return None

    def save_post(self, content, filename, lang='ko'):
        date_dir = datetime.now().strftime('%Y/%m/%d')
        base_path = f"content/{lang}/posts/{date_dir}"
        os.makedirs(base_path, exist_ok=True)
        full_path = os.path.join(base_path, filename)
        with open(full_path, "w", encoding="utf-8-sig") as f:
            f.write(content)
        logger.info(f"Article Saved: {full_path}")
        return True
