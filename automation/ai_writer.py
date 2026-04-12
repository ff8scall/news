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

    def _generate_api_call(self, prompt, provider="gemini", model_name=None):
        """[V11.0] 개별 API 호출 및 쿼터 제한 감지"""
        if provider in self.failed_providers:
            return None

        if provider == "gemini":
            if not self.gemini_key or not self.client: return None
            # [V12.3] 모델별 독립 쿼터 관리
            model_key = f"gemini:{model_name}" if model_name else "gemini:gemini-2.0-flash"
            if model_key in self.failed_providers: return None

            try:
                target_model = model_name if model_name else 'gemini-2.0-flash'
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
                return None
            except Exception as e:
                err_msg = str(e).lower()
                if "quota" in err_msg or "429" in err_msg:
                    print(f" [!] Gemini Model {target_model} Quota Exceeded. Disabling this model.")
                    self.failed_providers.add(model_key)
                else:
                    print(f" [!] Gemini Failure ({target_model}): {e}")
                return None
            
        elif provider == "deepseek":
            if not self.deepseek_key: return None
            try:
                target_model = model_name if model_name else "deepseek-chat"
                response = requests.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {self.deepseek_key.strip()}", "Content-Type": "application/json"},
                    data=json.dumps({
                        "model": target_model,
                        "messages": [{"role": "system", "content": "You are a professional tech editor. Output ONLY JSON."}, {"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }), timeout=60
                )
                if response.status_code == 429 or response.status_code == 402:
                    print(f" [!] DeepSeek Quota/Balance issue. Disabling.")
                    self.failed_providers.add("deepseek")
                    return None
                    
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                return None
            except Exception as e:
                print(f" [!] DeepSeek Failure: {e}")
                return None

        elif provider == "groq":
            if not self.groq_key: return None
            try:
                target_model = model_name if model_name else "llama-3.1-8b-instant"
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.groq_key.strip()}", "Content-Type": "application/json"},
                    data=json.dumps({
                        "model": target_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }), timeout=30
                )
                if response.status_code == 429:
                    print(f" [!] Groq Rate Limit reached. Disabling.")
                    self.failed_providers.add("groq")
                    return None
                    
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f" [!] groq Error Body: {data}")
                    return None
            except Exception as e:
                print(f" [!] groq Failure: {e}")
                return None
                
        elif provider == "openrouter":
            if not self.openrouter_key: return None
            try:
                target_model = model_name if model_name else "openai/gpt-4o-mini"
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openrouter_key.strip()}", "Content-Type": "application/json"},
                    data=json.dumps({
                        "model": target_model,
                        "messages": [{"role": "user", "content": prompt}]
                    }), timeout=60
                )
                if response.status_code in [402, 403, 429]:
                    print(f" [!] OpenRouter Quota/Limit issue ({response.status_code}). Disabling.")
                    self.failed_providers.add("openrouter")
                    return None
                    
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f" [!] openrouter Error Body: {data}")
                    return None
            except Exception as e:
                print(f" [!] openrouter Failure: {e}")
                return None

        elif provider == "cloudflare":
            if not self.cf_account or not self.cf_token: return None
            try:
                target_model = model_name if model_name else "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
                url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account}/ai/run/{target_model}"
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.cf_token}", "Content-Type": "application/json"},
                    json={"messages": [{"role": "user", "content": prompt}]},
                    timeout=45
                )
                if response.status_code == 429:
                    print(f" [!] Cloudflare Rate Limit. Skipping.")
                    self.failed_providers.add("cloudflare")
                    return None
                
                data = response.json()
                if data.get("success") and "result" in data:
                    return data["result"]["response"]
                else:
                    print(f" [!] Cloudflare Error Body: {data}")
                    return None
            except Exception as e:
                print(f" [!] Cloudflare Failure: {e}")
                return None
        
        elif provider == "github":
            if not self.github_token: return None
            try:
                target_model = model_name if model_name else "gpt-4o-mini"
                url = "https://models.inference.ai.azure.com/chat/completions"
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.github_token}", "Content-Type": "application/json"},
                    json={
                        "model": target_model,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=30
                )
                if response.status_code == 429:
                    print(f" [!] GitHub Models Rate Limit. Skipping.")
                    self.failed_providers.add("github")
                    return None
                
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f" [!] GitHub Models Error: {data}")
                    return None
            except Exception as e:
                print(f" [!] GitHub Models Failure: {e}")
                return None
        return None

    def generate_content(self, prompt, category="AI·신기술", model=None):
        # [V12.4 Verified] 검증된 고효율 모델 우선 배치 (Gemini Quota Maximization)
        candidates = [
            ("gemini", "gemini-3.1-flash-lite-preview"), # RPD 500 (최우선)
            ("gemini", "gemini-3-flash-preview"),        # RPD 20
            ("gemini", "gemini-2.5-flash"),              # Verified
            ("gemini", "gemini-2.5-flash-lite"),         # Verified (429-aware)
            ("gemini", "gemini-2.0-flash"),              # Verified (429-aware)
            ("gemini", "gemini-2.0-flash-lite"),         # Verified (429-aware)
            ("github", "gpt-4o-mini"),                   # 안정적인 백업
            ("gemini", "gemini-3.1-pro-preview"),
            ("gemini", "gemini-3-pro-preview"),
            ("cloudflare", "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"),
            ("openrouter", "openai/gpt-4o-mini"),
            ("groq", "llama-3.1-8b-instant"),
            ("deepseek", "deepseek-chat")
        ]
        
        # 특정 모델이 요청된 경우 최우선 순위로 삽입
        if model:
            # 모델명으로 공급자 유추
            inferred_provider = "gemini" if "gemini" in model else "openrouter"
            if "llama" in model: inferred_provider = "groq"
            if "deepseek" in model: inferred_provider = "deepseek"
            candidates.insert(0, (inferred_provider, model))

        for provider, model_name in candidates:
            # [V12.3] 모델별 실패 여부 체크 로직 정밀화
            check_key = f"{provider}:{model_name}" if provider == "gemini" else provider
            if check_key in self.failed_providers:
                continue
                
            try:
                # print(f" [*] Attempting {provider} ({model_name})...")
                res = self._generate_api_call(prompt, provider, model_name=model_name)
                if res and len(res.strip()) > 10:
                    self.usage_stats[provider] += 1
                    print(f" [OK] Content generated via {provider} ({model_name})")
                    return res
            except Exception as e:
                print(f" [!] {provider} cycle failed: {e}")
            
            # API 보호를 위한 지연 (성공 시에는 NewsEditor에서 처리하므로 실패 시에만 최소한의 대기)
            if provider not in self.failed_providers:
                time.sleep(2) # 실패했으나 밴되지 않은 경우만 약간 대기
            
        return None

    def is_all_exhausted(self):
        """[V12.4] 주요 모델 소진 여부 광범위 체크"""
        core_providers = [
            "github", 
            "gemini:gemini-3.1-flash-lite-preview", 
            "openrouter", 
            "groq", 
            "deepseek"
        ]
        return all(p in self.failed_providers for p in core_providers)

    def save_post(self, content, filename):
        if not content: return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        posts_dir = os.path.join(base_dir, "content", "posts")
        os.makedirs(posts_dir, exist_ok=True)
        clean_content = content.replace("```markdown", "").replace("```", "").strip()
        with open(os.path.join(posts_dir, filename), "w", encoding="utf-8") as f:
            f.write(clean_content)

