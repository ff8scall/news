# -*- coding: utf-8 -*-
import re
from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    """
    Standardize URL to prevent duplicates (remove query params, fragments, etc.)
    """
    if not url: return ""
    try:
        parsed = urlparse(url)
        # Keep only scheme, netloc, path
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    except:
        return url

def clean_text(text):
    """
    Remove HTML tags and escape quotes for Hugo frontmatter
    """
    if not text: return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Replace double quotes with single for YAML safety
    text = text.replace('"', "'")
    # Remove extra whitespaces
    text = " ".join(text.split())
    return text

def extract_domain(url):
    """
    Extract source domain for weighting
    """
    try:
        return urlparse(url).netloc.replace('www.', '')
    except:
        return "Unknown"

def send_telegram_report(message: str) -> bool:
    """
    [V1.1] Production Reporting: Dispatches execution summaries to Telegram.
    Uses the direct Telegram Bot API for maximum reliability within the script.
    """
    import os
    import requests
    from dotenv import load_dotenv
    
    # Ensure environment variables are loaded
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print(f"[Telegram] Missing credentials (Chat ID: {'Set' if chat_id else 'Not Set'}, Token: {'Set' if token else 'Not Set'}). Skipping notification.")
        return False
        
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            msg_snippet = message.split('\n')[0][:30]
            try:
                print(f"[Telegram] Report dispatched successfully. ({msg_snippet}...)")
            except UnicodeEncodeError:
                print(f"[Telegram] Report dispatched successfully. (Encoding error in snippet)")
            return True
        else:
            print(f"[Telegram] Failed to send report. Status: {response.status_code}")
            return False
    except Exception as e:
        try:
            print(f"[Telegram] Connection Error: {e}")
        except UnicodeEncodeError:
            print(f"[Telegram] Connection Error: (Encoding error in message)")
        return False

def sanitize_slug(text: str) -> str:
    """
    [V2.0] Hybrid SEO-Friendly URL Generator: 
    Converts titles to clean slugs. Fallbacks to hash for non-ASCII titles.
    """
    if not text: return "unnamed-post"
    
    # 1. Try to normalize to ASCII (works for EN titles)
    import unicodedata
    import hashlib
    
    norm_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', norm_text).strip('-')
    
    # 2. If title was mostly non-ASCII (like Korean), slug will be empty or too short
    if len(slug) < 3:
        # Fallback: create a slug using the date/category or just a hash
        h = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"feature-{h}"
    
    return slug
