from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def gmail_login():
    """
    Authenticate the user using OAuth2 and return a Gmail API service object.
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials/gmail_credentials.json",
        SCOPES
    )
    creds = flow.run_local_server(port=0)
    service = build("gmail", "v1", credentials=creds)
    return service

def create_message(to, subject, message_text):
    """
    Create a MIME email message ready for sending.

    Args:
        to (str or list): Recipient email address(es).
        subject (str): Email subject line.
        message_text (str): Body of the email.

    Returns:
        dict: A dictionary with the raw MIME message.
    """
    message = MIMEText(message_text)
    if isinstance(to, list):
        message["to"] = ", ".join(to)
    else:
        message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}

def send_email(service, message):
    """
    Send an email using the authenticated Gmail service.

    Args:
        service: Gmail API service instance.
        message (dict): MIME message created by create_message().
    """
    service.users().messages().send(userId="me", body=message).execute()