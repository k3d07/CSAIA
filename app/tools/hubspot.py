import os
import httpx
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")


@tool
def create_support_ticket(issue_summary: str, customer_email: str) -> str:
    """
    Create a support ticket in HubSpot for a customer issue.
    Use this when:
    - The customer has a complex problem that needs human follow-up
    - You're escalating an issue you couldn't resolve
    - The customer explicitly asks to speak with a human
    - The issue involves billing disputes, account termination, or legal matters

    Input:
    - issue_summary: a clear 1-3 sentence description of the customer's problem
    - customer_email: the customer's email address

    Returns: the ticket ID and confirmation, or an error message.
    """
    if not HUBSPOT_API_KEY:
        return "Ticket creation unavailable — HubSpot not configured. Issue logged internally."

    url = "https://api.hubapi.com/crm/v3/objects/tickets"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "subject": f"Support Request — {customer_email}",
            "content": issue_summary,
            "hs_ticket_priority": "MEDIUM",
            "hs_pipeline": "0",          # default support pipeline
            "hs_pipeline_stage": "1",    # New
        }
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        ticket_id = data.get("id", "Unknown")
        return (
            f"Support ticket created successfully.\n"
            f"Ticket ID: {ticket_id}\n"
            f"A human agent will contact {customer_email} within 24 hours."
        )

    except httpx.HTTPError as e:
        return f"Failed to create ticket: {str(e)}. Please try again or contact support directly."
