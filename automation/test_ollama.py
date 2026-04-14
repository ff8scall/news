import requests
import json

url = "http://localhost:11434/api/generate"
data = {
    "model": "gemma4:latest",
    "prompt": "Hello",
    "stream": False
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
