import os
import requests
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("VERTEX_KEY_API_KEY")
headers = {"Authorization": f"Bearer {key}"}

endpoints = [
    "https://vertex-key.com/api/v1/chat/completions",
    "https://vertex-key.com/v1/chat/completions",
    "https://vertex-key.com/api/chat/completions",
    "https://api.vertex-key.com/v1/chat/completions", # original
]

payload = {
    "model": os.getenv("VERTEX_KEY_MODEL_NAME", "aws/claude-haiku-4-5"),
    "messages": [{"role": "user", "content": "hello"}]
}

for ep in endpoints:
    print(f"\nTesting endpoint: {ep}")
    try:
        res = requests.post(ep, json=payload, headers=headers, timeout=5)
        print("Status code:", res.status_code)
        print("Response text:", res.text[:200])
    except Exception as e:
        print("Error:", e)
