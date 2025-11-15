import os
from functools import lru_cache

import google.generativeai as genai


@lru_cache(maxsize=1)
def _configured():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=api_key)
    return True


def generate_analysis(prompt: str) -> str:
    _configured()
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text or ""


