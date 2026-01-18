from google import genai
import os

# API Key
GEMINI_API_KEY = "AIzaSyB2O9xhxWEVwEEt9GpOss-YhW5JQX2Hf2s"

client = genai.Client(api_key=GEMINI_API_KEY)

print("Listing available models:")
try:
    for m in client.models.list():
        print(f" - {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")