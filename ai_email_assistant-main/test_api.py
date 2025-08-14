import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app_key = os.getenv("OPENROUTER_API_KEY")
print("API key loaded:", app_key[:10] + "..." if app_key else "❌ Not found")

# Prepare request
headers = {
    "Authorization": f"Bearer {app_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "mistralai/mistral-7b-instruct:free",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello!"}
    ]
}

# Send request
try:
    res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                        headers=headers, data=json.dumps(payload))
    print("Status code:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
