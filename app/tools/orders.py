import os
import httpx
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Orders")


@tool
def get_order_status(order_id: str) -> str:
    """
    Look up the status of a customer's order by order ID.
    Use this when the customer mentions an order number, asks about
    a specific purchase, wants a delivery update, or asks why their
    order hasn't arrived.

    Input: the order ID string exactly as the customer provided it.
    Returns: order status, date, and any tracking information,
    or a message that the order was not found.

    Do NOT use this for general policy questions — use search_faq instead.
    """
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        # Graceful fallback for demo without Airtable configured
        return (
            f"Order lookup is currently unavailable. "
            f"Order ID '{order_id}' could not be verified. "
            f"Please escalate this to a human agent."
        )

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {"filterByFormula": f"{{OrderID}} = '{order_id}'"}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        records = data.get("records", [])
        if not records:
            return f"No order found with ID: {order_id}. Please verify the order ID and try again."

        record = records[0]["fields"]
        return (
            f"Order {order_id} found:\n"
            f"Status: {record.get('Status', 'Unknown')}\n"
            f"Order Date: {record.get('OrderDate', 'Unknown')}\n"
            f"Product: {record.get('Product', 'Unknown')}\n"
            f"Estimated Delivery: {record.get('EstimatedDelivery', 'Unknown')}\n"
            f"Tracking Number: {record.get('TrackingNumber', 'Not yet assigned')}"
        )

    except httpx.HTTPError as e:
        return f"Order lookup failed due to a technical error: {str(e)}. Please escalate."
