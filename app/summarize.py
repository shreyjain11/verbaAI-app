# app/summarize.py

import os
from dotenv import load_dotenv
from openai import OpenAI

# 1) Load .env into os.environ
load_dotenv()

# 2) Instantiate the OpenAI client with the API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_to_email(transcribed_text: str) -> str:
    prompt = f"""
Given the following transcript, write a professional email body only (no subject line, no closing signature).
Be concise, polite, and organize key points into bullets if needed.

Transcript:
{transcribed_text}

Email Body (No Subject Line, No Signature):
"""
    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
