from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
print("Client initialized")
try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=["Hello"]
    )
    print("Success:", response.text)
except Exception as e:
    print("Error:", type(e).__name__, repr(e))
