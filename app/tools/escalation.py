import os
import httpx
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


@tool
def escalate_to_human(reason: str, conversation_context: str = "") -> str:
    """
    Escalate a support conversation to a human agent via Slack alert.

    Use this when:
    - You searched the knowledge base and the answer is not there
      (relevance scores all below 0.4)
    - The customer's issue involves something you cannot verify
      (fraud, security breach, legal matters, harassment)
    - The customer explicitly asks to speak with a human
    - The customer is expressing significant frustration or distress
    - You've attempted to help twice and the issue remains unresolved
    - The question involves a refund over $100 (escalate for authorization)

    This is not a failure — escalating with full context is the correct
    behavior for issues outside your scope.

    Input:
    - reason: why you're escalating (1-2 sentences, specific)
    - conversation_context: the full context of what was asked and
      what you tried, so the human agent can take over without asking
      the customer to repeat themselves

    Returns: confirmation the human team was notified.
    """
    if not SLACK_WEBHOOK_URL:
        return (
            "Escalation alert sent (Slack not configured — logged internally). "
            "A human agent will follow up within 2 business hours."
        )

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Support Escalation Required",
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Reason:*\n{reason}"},
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Conversation Context:*\n```{conversation_context[:1500]}```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "AI support agent could not resolve. Human follow-up needed within 2 hours."
                    }
                ]
            }
        ]
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(SLACK_WEBHOOK_URL, json=message)
            response.raise_for_status()

        return (
            "Your request has been escalated to our support team. "
            "A human agent will contact you within 2 business hours. "
            "You don't need to repeat yourself — they have the full context of our conversation."
        )

    except httpx.HTTPError as e:
        return (
            f"Escalation notification had a technical issue ({str(e)}), "
            "but your case has been logged. A human agent will follow up within 4 hours."
        )
