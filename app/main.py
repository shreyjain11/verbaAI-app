# app/main.py

import os
import streamlit as st
import requests
from dotenv import load_dotenv
from streamlit_lottie import st_lottie
from app.transcribe import transcribe_audio
from app.summarize import summarize_to_email
from app.email_utils import gmail_login, create_message, send_email

load_dotenv()

# ——— Constants ———
CONTACTS = {
    "Boss":     "boss@example.com",
    "Client":   "client@example.com",
    "Coworker": "coworker@example.com",
    "Myself":   "mailshreyjain@gmail.com"
}
AUDIO_PATH = "static/temp_audio.wav"

# ——— Helpers ———
def load_css(path: str):
    """Inject local CSS file into the app."""
    if os.path.exists(path):
        with open(path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_data
def load_lottie_url(url: str):
    """Fetch a Lottie JSON from a URL (cached)."""
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def save_uploaded_audio(uploaded, path: str):
    """Write uploaded audio file to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(uploaded.read())

# Resolve project root and logo path
HERE = os.path.dirname(__file__)                   # e.g. /Users/.../verbaAI/app
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
LOGO_PATH = os.path.join(PROJECT_ROOT, "logo.png")

logo_col, anim_col = st.columns([1, 2])
with logo_col:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=100)
    else:
        st.warning(f"⚠️ logo.png not found at:\n{LOGO_PATH}")
        
with anim_col:
    lottie = load_lottie_url(
        "https://assets9.lottiefiles.com/packages/lf20_ucbyrun5.json"
    )
    if lottie:
        st_lottie(lottie, height=120)

# Load your app/style.css (make sure this file lives at app/style.css)
load_css("app/style.css")

# Branded header
st.markdown(
    "<h1 style='text-align:center; color:#333;'>VerbaAI</h1>"
    "<p style='text-align:center; font-size:1.1em;'>"
    "Your AI-powered voice-to-email assistant"
    "</p>",
    unsafe_allow_html=True
)

# ——— User Profile Setup ———
def setup_user_profile():
    st.header("🛠️ Set Up Your Profile")
    name          = st.text_input("Your Full Name")
    title         = st.text_input("Your Title/Position (optional)")
    contact_email = st.text_input("Your Contact Email")
    phone_number  = st.text_input("Your Phone Number (optional)")

    if st.button("Save Profile and Continue ➡️"):
        if name.strip() and contact_email.strip():
            st.session_state.user_profile = {
                "name":  name.strip(),
                "title": title.strip(),
                "email": contact_email.strip(),
                "phone": phone_number.strip()
            }
            st.success("✅ Profile saved!")
            st.experimental_rerun()
        else:
            st.error("⚠️ Name and Email are required.")

# ——— Main App Flow ———
def main_app():
    prof = st.session_state.user_profile
    st.header(f"🎯 Hello, {prof['name']}!")
    st.subheader("Step 1: Upload your audio file")

    uploaded = st.file_uploader("Upload a .wav or .mp3", type=["wav", "mp3"])
    if uploaded:
        save_uploaded_audio(uploaded, AUDIO_PATH)
        st.success("✅ Audio uploaded, processing…")
        try:
            transcript = transcribe_audio(AUDIO_PATH)
            st.session_state.transcript = transcript

            draft = summarize_to_email(transcript)
            sig  = f"\n\nBest regards,\n{prof['name']}"
            if prof.get("title"): sig += f"\n{prof['title']}"
            sig += f"\n{prof['email']}"
            if prof.get("phone"): sig += f"\n{prof['phone']}"

            st.session_state.email_draft = draft + sig
            st.success("✅ Transcript and draft ready!")
        except Exception as e:
            st.error(f"Error during processing: {e}")

    if "transcript" in st.session_state:
        st.subheader("📜 Transcript")
        st.text_area("", st.session_state.transcript, height=200)

        st.subheader("✍️ Email Draft")
        st.session_state.email_draft = st.text_area("", st.session_state.email_draft, height=250)

        st.subheader("👥 Recipients")
        chosen = st.multiselect("Pick saved contacts:", list(CONTACTS.keys()))
        custom = st.text_input("Or enter a custom email:")

        recips = [CONTACTS[n] for n in chosen]
        if custom.strip(): recips.append(custom.strip())

        subject = st.text_input("Subject Line")

        if st.button("📨 Send Email"):
            if recips and subject.strip() and st.session_state.email_draft.strip():
                try:
                    svc = gmail_login()
                    msg = create_message(recips, subject.strip(), st.session_state.email_draft)
                    send_email(svc, msg)
                    st.success("✅ Email sent!")
                except Exception as e:
                    st.error(f"Failed to send: {e}")
            else:
                st.error("⚠️ Fill out all fields before sending.")

        if st.button("🔄 Reset"):
            st.session_state.clear()
            st.experimental_rerun()

# ——— Entrypoint ———
def main():
    if "user_profile" not in st.session_state:
        setup_user_profile()
    else:
        main_app()

if __name__ == "__main__":
    main()