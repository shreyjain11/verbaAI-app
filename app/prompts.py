def email_prompt(transcribed_text):
    return f"""
    Turn this spoken note into a professional email. Be concise, polite, and organize key points into bullets if needed.

    Transcript: {transcribed_text}

    Email:
    """