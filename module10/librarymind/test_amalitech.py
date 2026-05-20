import os
import urllib.request
import urllib.error
import json

url = "https://ai-api.amalitech.org/api/v2/public/v1/chat/completions"
api_key = os.environ.get("AMALITECH_API_KEY", "your-api-key-here")

headers = {
    "Provider": "openai",
    "X-Api-Key": api_key,
    "Content-Type": "application/json"
}
data = json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello"}], "stream": False}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:", response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode("utf-8"))
except Exception as e:
    print("ERROR:", e)

url2 = "https://ai-api.amalitech.org/api/v2/public/chat/completions"
req2 = urllib.request.Request(url2, data=data, headers=headers)
try:
    with urllib.request.urlopen(req2) as response:
        print("SUCCESS 2:", response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("HTTP ERROR 2:", e.code, e.read().decode("utf-8"))
except Exception as e:
    print("ERROR 2:", e)
