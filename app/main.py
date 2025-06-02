# app/main.py
import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from app.transcribe import transcribe_audio
from app.summarize import summarize_to_email
from app.email_utils import gmail_login, create_message, send_email

# Load environment variables (your OPENAI_API_KEY, etc.)
load_dotenv()

# Initialize OpenAI client once
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pre-saved contacts (you can pull these from a DB or file later)
CONTACTS = {
    "Boss": "boss@example.com",
    "Client": "client@example.com",
    "Coworker": "coworker@example.com",
    "Myself": st.session_state.get("user_profile", {}).get("email", "")
}

def setup_user_profile():
    """Show profile-setup form, save into session_state, then return."""
    st.image("logo.png", width=120)
    st.title("🛠 Set Up Your VerbaAI Profile")

    name          = st.text_input("Your Full Name")
    title         = st.text_input("Your Title or Position (optional)")
    contact_email = st.text_input("Your Contact Email")
    phone         = st.text_input("Your Phone Number (optional)")

    if st.button("Save Profile and Continue ➡️"):
        if not name or not contact_email:
            st.error("Please enter at least your name and email.")
            return

        st.session_state.user_profile = {
            "name":  name,
            "title": title,
            "email": contact_email,
            "phone": phone
        }
        st.success("Profile saved!")
        return  # Streamlit will auto-rerun and drop into main_app()

def main_app():
    """Main voice-to-email flow once profile is set."""
    user = st.session_state.user_profile
    st.title(f"Hello, {user['name']}!")
    st.write("## Step 1: Provide your audio")

    mode = st.radio("Select how you'd like to provide audio:", ["Upload a File", "Record Now"])
    audio_path = None

    if mode == "Upload a File":
        upload = st.file_uploader("Choose a .wav or .mp3", type=["wav", "mp3"])
        if upload:
            audio_path = "static/temp_audio.wav"
            with open(audio_path, "wb") as f:
                f.write(upload.read())

    else:  # Record Now
        st.info("Click ▶️ Start Recording to begin, ◼️ Stop when done.")
        from streamlit_webrtc import webrtc_streamer  # pip install streamlit-webrtc
        ctx = webrtc_streamer(key="voice-recorder", audio_receiver_size=1024)
        if ctx and ctx.audio_receiver:
            # When user stops, grab frames and save
            frames = ctx.audio_receiver.get_frames(timeout=5)
            if frames:
                import soundfile as sf  # pip install soundfile
                data = b"".join([f.to_bytes() for f in frames])
                audio_path = "static/temp_audio.wav"
                with open(audio_path, "wb") as f:
                    f.write(data)
            else:
                st.warning("⚠No audio captured—try again.")
        else:
            st.write("Not recording")

    # If we have a file, transcribe & summarize
    if audio_path:
        st.info("🔊 Transcribing audio...")
        try:
            transcript = transcribe_audio(audio_path)
            st.subheader("Transcript")
            st.text_area("Full transcribed text", transcript, height=200)

            st.info("Generating email draft...")
            draft = summarize_to_email(transcript)
            # append signature
            sig = f"\n\nBest regards,\n{user['name']}"
            if user.get("title"):
                sig += f"\n{user['title']}"
            sig += f"\n{user['email']}"
            if user.get("phone"):
                sig += f"\n{user['phone']}"
            st.session_state.email_draft = draft + sig

        except Exception as e:
            st.error(f"Error: {e}")

    # Show & edit draft
    if "email_draft" in st.session_state:
        st.subheader("Email Draft")
        st.session_state.email_draft = st.text_area(
            "Edit your email", st.session_state.email_draft, height=250
        )

        st.subheader("Recipients")
        choices = st.multiselect("Select saved contacts:", list(CONTACTS.keys()))
        manual = st.text_input("Or enter a custom email")

        recipients = [CONTACTS[name] for name in choices]
        if manual:
            recipients.append(manual.strip())

        subject = st.text_input("Subject Line")

        if st.button("Send Email"):
            if not (recipients and subject and st.session_state.email_draft):
                st.error("Please fill out all fields before sending.")
            else:
                try:
                    service = gmail_login()
                    msg = create_message(recipients, subject, st.session_state.email_draft)
                    send_email(service, msg)
                    st.success("Email sent!")
                except Exception as err:
                    st.error(f"Failed to send: {err}")

        if st.button("Reset & Start Over"):
            for key in ["transcript", "email_draft"]:
                st.session_state.pop(key, None)
            return  # rerun to go back to Step 1

def main():
    if "user_profile" not in st.session_state:
        setup_user_profile()
    else:
        main_app()

if __name__ == "__main__":
    main()
