import os
import resend
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
# Sandbox FROM for demo (no domain verification needed).
# Change to your verified Resend domain for production.
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")


@tool
def send_reply_email(to_email: str, subject: str, body: str) -> str:
    """
    Send an email reply to a customer.
    Use this when the customer's question has been resolved and
    they would benefit from having the answer in their inbox,
    or when they explicitly ask for an email confirmation.

    Do NOT use this for every response — only when email follow-up
    genuinely adds value (e.g., sending them a refund confirmation,
    account change confirmation, or detailed instructions too long
    for the chat interface).

    Input:
    - to_email: recipient email address
    - subject: email subject line (keep under 60 characters)
    - body: full email body in plain text

    Returns: confirmation the email was sent, or an error.
    """
    if not os.getenv("RESEND_API_KEY"):
        return f"Email sending unavailable — Resend not configured. Would have emailed {to_email}."

    try:
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "text": body,
        })
        return f"Email sent successfully to {to_email}. Message ID: {response['id']}"

    except Exception as e:
        return f"Failed to send email: {str(e)}"
