import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("✅ Gemini SDK version:", genai.__version__)
print("Available models:")
for m in genai.list_models():
    if "gemini" in m.name:
        print("-", m.name)

model = genai.GenerativeModel("gemini-1.5-flash-latest")
response = model.generate_content("Write one line about AI and jobs.")
print("\nResponse:", response.text)
