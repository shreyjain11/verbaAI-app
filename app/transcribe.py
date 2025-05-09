# app/transcribe.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# load .env (so OPENAI_API_KEY gets picked up if you ever run locally)
load_dotenv()

# instantiate the client once
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(file_path: str) -> str:
    """
    Uploads your WAV/MP3 to OpenAI Whisper and returns the transcript text.
    """
    with open(file_path, "rb") as audio_file:
        # for openai>=1.0.0:
        response = _client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return response.text