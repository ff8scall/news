import os
import requests
import json
import time
from google import genai
from datetime import datetime
from dotenv import load_dotenv

# [V3.2] 절대 경로 기반 .env 로드 (윈도우 호환성 극대화)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

class AIWriter:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        # [V11.0] 서비스 상태 추적
        self.failed_providers = set()
        
        # 디버깅: 키 로드 상태 확인
        if self.gemini_key: print(f"[*] Gemini Key Loaded: {self.gemini_key[:8]}***")
        if self.deepseek_key: print(f"[*] DeepSeek Key Loaded: {self.deepseek_key[:8]}***")
        if self.groq_key: print(f"[*] Groq Key Loaded: {self.groq_key[:8]}***")
        if self.openrouter_key: print(f"[*] OpenRouter Key Loaded: {self.openrouter_key[:8]}***")
        
        # [V11.5] Cloudflare 전용 정보
        self.cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.cf_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if self.cf_account: print(f"[*] Cloudflare ID Loaded: {self.cf_account[:8]}***")
        
        # [V11.6] GitHub Models 전용 정보
        self.github_token = os.getenv("GH_MODELS_TOKEN")
        if self.github_token: print(f"[*] GitHub Models Token Loaded: {self.github_token[:10]}***")

        # [V12.0] New SDK Client
        self.client = None
        if self.gemini_key:
            try:
                self.client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                print(f" [!] Failed to initialize Gemini Client: {e}")

        # [V12.2] Usage Statistics
        self.usage_stats = {p: 0 for p in ["github", "cloudflare", "gemini", "openrouter", "groq", "deepseek"]}

        # [V12.5] Request Throttling (To respect 15 RPM limit)
        self.last_call_time = 0
        self.min_interval = 4.5  # 15 RPM = 4s interval, 4.5s for safety

    def _generate_api_call(self, prompt, provider="gemini", model_name=None):
        """[V12.5] Throttled API call with 429 retry logic"""
        # [Throttling] ensure minimum interval between any AI calls
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        if provider in self.failed_providers:
            return None

        # [V12.6] Retry logic for 429
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                self.last_call_time = time.time()
                
                if provider == "gemini":
                    if not self.gemini_key or not self.client: return None
                    model_key = f"gemini:{model_name}" if model_name else "gemini:gemini-2.0-flash"
                    if model_key in self.failed_providers: return None

                    target_model = model_name if model_name else 'gemini-2.0-flash'
                    response = self.client.models.generate_content(
                        model=target_model,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text
                    return None
                
                elif provider == "github":
                    if not self.github_token: return None
                    target_model = model_name if model_name else "gpt-4o-mini"
                    url = "https://models.inference.ai.azure.com/chat/completions"
                    response = requests.post(
                        url,
                        headers={"Authorization": f"Bearer {self.github_token}", "Content-Type": "application/json"},
                        json={"model": target_model, "messages": [{"role": "user", "content": prompt}]},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    elif response.status_code == 429:
                        raise Exception("429 Rate Limit")
                    else:
                        return None

                # ... (other providers similarly, keeping it concise for now or adding them back)
                # For brevity in this edit, I will focus on the core ones or keep existing logic template
                elif provider == "deepseek":
                    if not self.deepseek_key: return None
                    target_model = model_name if model_name else "deepseek-chat"
                    response = requests.post("https://api.deepseek.com/chat/completions",
                        headers={"Authorization": f"Bearer {self.deepseek_key.strip()}", "Content-Type": "application/json"},
                        json={"model": target_model, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
                    if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
                    if response.status_code in [429, 402]: raise Exception(f"{response.status_code} Error")
                    return None

                elif provider == "groq":
                    if not self.groq_key: return None
                    target_model = model_name if model_name else "llama-3.1-8b-instant"
                    response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.groq_key.strip()}", "Content-Type": "application/json"},
                        json={"model": target_model, "messages": [{"role": "user", "content": prompt}]}, timeout=30)
                    if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
                    if response.status_code == 429: raise Exception("429 Error")
                    return None

                elif provider == "openrouter":
                    if not self.openrouter_key: return None
                    target_model = model_name if model_name else "openai/gpt-4o-mini"
                    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.openrouter_key.strip()}", "Content-Type": "application/json"},
                        json={"model": target_model, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
                    if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
                    if response.status_code in [402, 429]: raise Exception(f"{response.status_code} Error")
                    return None

                elif provider == "cloudflare":
                    if not self.cf_account or not self.cf_token: return None
                    target_model = model_name if model_name else "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
                    url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account}/ai/run/{target_model}"
                    response = requests.post(url, headers={"Authorization": f"Bearer {self.cf_token}"},
                        json={"messages": [{"role": "user", "content": prompt}]}, timeout=45)
                    data = response.json()
                    if data.get("success"): return data["result"]["response"]
                    if response.status_code == 429: raise Exception("429 Error")
                    return None

            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg:
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 10
                        print(f" [!] {provider} 429 detected. Retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f" [!] {provider} still failing after retries. Banning for session.")
                        key = f"gemini:{model_name}" if provider == "gemini" else provider
                        self.failed_providers.add(key)
                elif "402" in err_msg or "balance" in err_msg or "quota" in err_msg:
                    print(f" [!] {provider} Quota/Balance exhausted. Banning.")
                    key = f"gemini:{model_name}" if provider == "gemini" else provider
                    self.failed_providers.add(key)
                else:
                    print(f" [!] {provider} Error: {e}")
                return None
        return None

    def generate_content(self, prompt, category="AI·신기술", model=None):
        # [V12.6] Stability-First Candidate Order
        candidates = [
            ("gemini", "gemini-3.1-flash-lite-preview"),
            ("github", "gpt-4o-mini"),                   # Reliable high-quota backup
            ("groq", "llama-3.1-8b-instant"),            # Fast failover
            ("gemini", "gemini-2.0-flash-lite"),
            ("gemini", "gemini-2.0-flash"),
            ("openrouter", "openai/gpt-4o-mini"),
            ("cloudflare", "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"),
            ("deepseek", "deepseek-chat")
        ]
        
        if model:
            inferred_provider = "gemini" if "gemini" in model else "openrouter"
            if "llama" in model: inferred_provider = "groq"
            if "deepseek" in model: inferred_provider = "deepseek"
            # Ensure custom model isn't tried if already failed
            check_key = f"{inferred_provider}:{model}" if inferred_provider == "gemini" else inferred_provider
            if check_key not in self.failed_providers:
                candidates.insert(0, (inferred_provider, model))

        for provider, model_name in candidates:
            check_key = f"{provider}:{model_name}" if provider == "gemini" else provider
            if check_key in self.failed_providers:
                continue
                
            res = self._generate_api_call(prompt, provider, model_name=model_name)
            if res and len(res.strip()) > 10:
                self.usage_stats[provider] += 1
                return res
            
        return None

    def is_all_exhausted(self):
        """[V12.5] Check if ALL reliable providers are down"""
        # We check Gemini Flash Lite and GitHub (the two main free/high-quota ones)
        # and also a few backups.
        essential = ["gemini:gemini-3.1-flash-lite-preview", "github", "groq"]
        return all(p in self.failed_providers for p in essential)

    def save_post(self, content, filename):
        if not content: return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        posts_dir = os.path.join(base_dir, "content", "posts")
        os.makedirs(posts_dir, exist_ok=True)
        clean_content = content.replace("```markdown", "").replace("```", "").strip()
        with open(os.path.join(posts_dir, filename), "w", encoding="utf-8") as f:
            f.write(clean_content)

