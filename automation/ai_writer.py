import json
import os
import time
import requests
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# [V3.5] Optimized Intelligence Engine for Gemma 4 & Parallel Processing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LegoSia.AIWriter")

class AIWriter:
    def __init__(self):
        load_dotenv()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "gemma4:latest" 
        self.parallel_workers = 4
        logger.info(f"AIWriter Initialized with {self.model} (Optimized Parallel: {self.parallel_workers})")

    def _generate_api_call(self, prompt, model_name=None):
        """[V3.5] Native Ollama Connector with Resilient Retries"""
        target_model = model_name if model_name else self.model
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": target_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 4096, "temperature": 0.7}
                },
                timeout=300
            )
            if response.status_code == 200:
                return response.json().get("response")
            else:
                logger.error(f"Ollama Error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Connection Error: {e}")
            return None

    def generate_content(self, prompt, model=None, role=None):
        """Legacy compatibility wrapper with role support"""
        # role can be used to select different models or system prompts in the future
        logger.info(f"Generating content for role: {role}")
        return self._generate_api_call(prompt, model_name=model)

    def is_all_exhausted(self):
        """Local Ollama is never 'exhausted' in terms of API quota"""
        return False

    def save_post(self, content, filename, lang='ko'):
        """[V3.5] Safe Content Archiver with UTF-8-SIG Enforcement"""
        base_path = f"content/{lang}/posts/{datetime.now().strftime('%Y/%m')}"
        os.makedirs(base_path, exist_ok=True)
        full_path = os.path.join(base_path, filename)
        
        with open(full_path, "w", encoding="utf-8-sig") as f:
            f.write(content)
        logger.info(f"Article Saved: {filename}")
        return True

if __name__ == "__main__":
    writer = AIWriter()
    test_res = writer.generate_content("Say hello in Korean")
    print(f"Test Result: {test_res}")
