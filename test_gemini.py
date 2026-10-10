import os, time
from dotenv import load_dotenv
load_dotenv()
from google import genai
from docurag.config import get_settings

s = get_settings()
key = s.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
model = getattr(s, "GEMINI_MODEL", None) or "gemini-3.5-flash"
print("model:", model, "| key set:", bool(key))

client = genai.Client(api_key=key)
t = time.time()
try:
    r = client.models.generate_content(model=model, contents="Say hello in five words.")
    print("OK:", r.text, f"({time.time()-t:.1f}s)")
except Exception as e:
    print("FAILED:", type(e).__name__, e)
