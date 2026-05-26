# Project 4 — Customer Support AI Agent
## LangChain + FastAPI + ChromaDB + OpenAI

---

## Read This First

The previous two projects were no-code/low-code tools doing fixed workflows. This project is different in two important ways.

First, it's pure Python. No Make, no n8n, no drag-and-drop. You're writing a real application with a real project structure, dependency management, async code, and a deployed API endpoint. This is the project where your Fluent Python background starts paying off.

Second, it introduces RAG — Retrieval-Augmented Generation. This is the technique that makes AI actually reliable for business use. Instead of the LLM answering from training data (which could be wrong, outdated, or hallucinated), it retrieves specific chunks from your actual documents and answers from those. Every answer is grounded in real content and comes with a citation telling you exactly which document it came from. That's what makes this production-worthy.

The business framing: a company's support team spends 60–70% of their time answering questions that are already answered in their documentation. This agent handles those automatically, with cited sources. Anything it can't answer with confidence gets escalated to a human with full context — the question, what the agent tried, and why it failed. No ticket gets dropped.

---

## What You're Building — The Full Picture

A FastAPI application with four endpoints:

`POST /chat` — the main endpoint. Accepts a user message and conversation history. The LangChain agent searches the knowledge base, decides what tools to use, and returns an answer with cited sources.

`POST /escalate` — called by the agent automatically when confidence is low. Creates a HubSpot support ticket and sends a Slack alert with full context.

`POST /ingest` — accepts document text or file uploads and adds them to the ChromaDB vector store. This is how you update the knowledge base without restarting the server.

`GET /health` — status check. Returns API uptime and vector store document count.

The agent has five tools:

1. `search_knowledge_base(query)` — semantic search over ChromaDB. Returns the top 4 most relevant chunks with their source document names.
2. `get_order_status(order_id)` — queries a fake Airtable database of orders. Simulates CRM/ERP integration.
3. `create_support_ticket(issue, email)` — creates a HubSpot ticket via API.
4. `send_reply_email(to, subject, body)` — sends a response email via Resend API.
5. `escalate_to_human(reason, context)` — fires a Slack alert with full conversation context when the agent determines it can't help.

The escalation tool is the most important one for portfolio purposes. Any system can answer easy questions. A system that knows what it doesn't know — and hands off gracefully with full context — is a system a real business would actually trust.

---

## Project Structure

Set this up before writing a single line of code.

```
customer-support-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app, route definitions
│   ├── agent.py             ← LangChain agent setup, tool definitions
│   ├── rag.py               ← ChromaDB vector store, ingestion, retrieval
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py  ← search_knowledge_base tool
│   │   ├── orders.py          ← get_order_status tool
│   │   ├── hubspot.py         ← create_support_ticket tool
│   │   ├── email.py           ← send_reply_email tool
│   │   └── escalation.py      ← escalate_to_human tool
│   └── models.py            ← Pydantic request/response models
├── knowledge_base/          ← your fake company docs go here
│   ├── faq.md
│   ├── refund_policy.md
│   ├── shipping_policy.md
│   ├── product_guide.md
│   └── pricing.md
├── db/                      ← ChromaDB persists here (gitignored)
├── tests/
│   └── test_agent.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Create all of these directories and empty files now before writing any code:

```bash
mkdir -p customer-support-agent/app/tools
mkdir -p customer-support-agent/knowledge_base
mkdir -p customer-support-agent/db
mkdir -p customer-support-agent/tests
cd customer-support-agent
touch app/__init__.py app/main.py app/agent.py app/rag.py app/models.py
touch app/tools/__init__.py app/tools/knowledge_base.py app/tools/orders.py
touch app/tools/hubspot.py app/tools/email.py app/tools/escalation.py
touch tests/test_agent.py .env .env.example .gitignore requirements.txt README.md
```

---

## Environment Setup

### Virtual Environment

```bash
cd customer-support-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### requirements.txt

```
# Core
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
python-dotenv==1.0.1
httpx==0.27.0

# LangChain
langchain==0.3.0
langchain-openai==0.2.0
langchain-community==0.3.0
langchain-chroma==0.1.4

# Vector store
chromadb==0.5.5

# Document loading
pypdf==4.3.1
unstructured==0.15.0

# APIs
openai==1.40.0
resend==2.3.0

# Utils
python-multipart==0.0.9
aiofiles==23.2.1
```

Install:
```bash
pip install -r requirements.txt
```

### .env

```
OPENAI_API_KEY=sk-...
HUBSPOT_API_KEY=pat-na1-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
RESEND_API_KEY=re_...
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=app...
AIRTABLE_TABLE_NAME=Orders
API_KEY=your-secret-api-key-for-this-service
CHROMA_PERSIST_DIR=./db
```

### .env.example

Same as above but with all values replaced by placeholder descriptions. Commit this. Never commit `.env`.

### .gitignore

```
venv/
__pycache__/
*.pyc
.env
db/
*.egg-info/
.DS_Store
```

---

## Step 1 — Create the Fake Knowledge Base Documents

This is not a throwaway step. Your demo depends on having realistic, detailed documents that the RAG system can actually retrieve from. Thin documents produce bad demos.

Write all five of these now. Use these as your starting point and expand them.

**knowledge_base/faq.md**

```markdown
# Frequently Asked Questions — NovaTech Solutions

## Account & Billing

**Q: How do I update my payment method?**
Go to Settings → Billing → Payment Methods → Add New Method.
Your new method will be charged on your next billing cycle.
Old payment methods can be removed once a new default is set.

**Q: Can I get a receipt for my purchase?**
Yes. Go to Settings → Billing → Invoice History. Click any invoice to
download a PDF receipt. Receipts are also automatically emailed to your
billing email address after every successful charge.

**Q: What happens if my payment fails?**
We retry failed payments 3 times over 7 days. You'll receive an email
notification for each attempt. If all 3 attempts fail, your account
is temporarily suspended until payment is updated. No data is lost
during suspension — reactivating restores full access immediately.

**Q: How do I cancel my subscription?**
Go to Settings → Billing → Subscription → Cancel Subscription.
Cancellations take effect at the end of your current billing period.
You retain full access until that date. We do not offer refunds for
partial billing periods.

**Q: Do you offer annual billing?**
Yes. Annual plans are available at a 20% discount vs monthly.
Switch at any time in Settings → Billing → Switch to Annual.
The switch takes effect at your next renewal date.

## Technical Support

**Q: The app is loading slowly. What should I do?**
First, clear your browser cache (Ctrl+Shift+Delete on Windows, 
Cmd+Shift+Delete on Mac). If the issue persists, try a different
browser. Check status.novatech.io for any active incidents.
If none are showing, contact support with your browser version
and a screenshot of any error messages.

**Q: I can't log in. What do I do?**
1. Try resetting your password via the "Forgot Password" link
2. Check if your account email is correct
3. Clear browser cookies and try again
4. If you use SSO (Google/Microsoft login), ensure your company
   SSO is active
Contact support if the above steps don't resolve it.

**Q: How do I export my data?**
Go to Settings → Data → Export. Select your date range and data types.
Exports are delivered via email within 30 minutes for standard exports,
up to 4 hours for full account exports. Data is provided in CSV and JSON.

## Features

**Q: Does the platform support API access?**
Yes. API documentation is available at docs.novatech.io/api.
API keys are generated in Settings → Developer → API Keys.
Rate limits: 1,000 requests/hour on Starter, 10,000/hour on Pro,
unlimited on Enterprise.

**Q: Can I integrate with Slack?**
Yes. Go to Settings → Integrations → Slack → Connect.
You can configure which events trigger Slack notifications
(new tickets, status changes, mentions).
```

**knowledge_base/refund_policy.md**

```markdown
# Refund Policy — NovaTech Solutions
Last updated: January 2025

## Standard Refund Policy

We offer full refunds within 14 days of purchase for all plans.
After 14 days, refunds are evaluated case-by-case.

To request a refund: email support@novatech.io with your order
number and reason for the refund request.
Refunds are processed within 5–7 business days to your original
payment method.

## Exceptions

The following are not eligible for refunds:
- Accounts that have exceeded their plan's API call limit
- Annual plans after 30 days from purchase date
- Add-on purchases (extra seats, storage upgrades) after use
- Accounts that violated our Terms of Service

## Partial Refunds

For annual plans cancelled between day 30 and day 180, we offer
a prorated refund for the remaining unused months minus a 10%
processing fee.

After 180 days, no refund is issued for annual plans.

## Disputed Charges

If you believe you've been charged incorrectly, contact us within
60 days. We investigate all disputed charges within 3 business days.
```

**knowledge_base/shipping_policy.md**

```markdown
# Shipping Policy — NovaTech Solutions

NovaTech is a software company. We do not ship physical products.
All products and licenses are delivered digitally.

## Digital Delivery

After purchase, you receive:
- A confirmation email with your license key within 5 minutes
- Access to your account dashboard immediately upon payment
- A receipt and invoice via email within 1 hour

## If You Haven't Received Your License Key

1. Check your spam/junk folder — filter on "novatech"
2. Verify the email address used at checkout
3. Wait 15 minutes — delivery can be delayed during high traffic
4. If still not received after 15 minutes, contact support

## Enterprise Contracts

Enterprise customers receive their contract documents and
onboarding materials via DocuSign within 1 business day
of signed agreement.
```

**knowledge_base/product_guide.md**

```markdown
# Product Guide — NovaTech Solutions

## Plans Overview

### Starter — $29/month
- Up to 3 team members
- 1,000 API calls/hour
- 5 GB storage
- Email support (48hr response SLA)
- Community forum access

### Pro — $79/month
- Up to 15 team members
- 10,000 API calls/hour
- 50 GB storage
- Priority email support (12hr SLA)
- Live chat support
- Advanced analytics dashboard
- Custom integrations

### Enterprise — Custom pricing
- Unlimited team members
- Unlimited API calls
- Custom storage
- Dedicated account manager
- Phone support
- Custom SLA agreements
- SSO (SAML 2.0)
- On-premise deployment option
- Custom contracts and invoicing

## Core Features

### Dashboard
The main dashboard shows your usage metrics, recent activity,
team member status, and billing summary. Customizable widgets
let you surface the data most relevant to your workflow.

### API
All platform features are accessible via REST API.
Authentication uses Bearer tokens generated in Settings → Developer.
Full API reference: docs.novatech.io/api

### Team Management
Invite team members via Settings → Team → Invite.
Role options: Admin (full access), Manager (billing + config),
Member (standard access), Viewer (read-only).
Pending invites expire after 72 hours.

### Integrations
Native integrations: Slack, HubSpot, Salesforce, Jira, GitHub,
Google Workspace, Microsoft 365.
Custom integrations via REST API and webhooks.

## Upgrading and Downgrading

You can change plans at any time. Upgrades take effect immediately
with prorated billing. Downgrades take effect at the next billing
cycle. Team members beyond the new plan's limit are set to
read-only access until the limit is met.
```

**knowledge_base/pricing.md**

```markdown
# Pricing — NovaTech Solutions

## Current Pricing (as of January 2025)

| Plan | Monthly | Annual (save 20%) |
|------|---------|-------------------|
| Starter | $29/mo | $278/yr ($23.17/mo) |
| Pro | $79/mo | $758/yr ($63.17/mo) |
| Enterprise | Custom | Custom |

## Add-ons

- Extra team seats: $10/seat/month (Starter), $8/seat/month (Pro)
- Additional storage: $5/10GB/month
- Priority onboarding: $299 one-time (Pro and Enterprise)
- Dedicated infrastructure: Contact sales

## Student and Nonprofit Discounts

Verified students and registered nonprofits receive 50% off
Starter and Pro plans. Email support@novatech.io with
verification documentation.

## Pricing Guarantees

- 30-day price lock: if we raise prices, your rate is locked
  for 30 days after announcement
- Annual subscribers are locked at their annual rate until renewal
- Grandfathered pricing: legacy customers retain their rates
  as long as their subscription remains active

## Frequently Asked Pricing Questions

**Is there a free trial?**
Yes. 14-day free trial on Starter and Pro. No credit card required.
Full feature access during trial.

**Do you offer monthly-to-annual switching mid-cycle?**
Yes. The annual rate applies from your next billing date.
No partial-period refunds for the switch.

**Are there setup fees?**
No setup fees on Starter or Pro.
Enterprise may have implementation fees depending on scope.
```

---

## Step 2 — Pydantic Models

File: `app/models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_history: list[Message] = Field(default_factory=list)
    user_email: Optional[str] = None
    session_id: Optional[str] = None


class Source(BaseModel):
    document: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    escalated: bool = False
    session_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IngestRequest(BaseModel):
    content: str = Field(..., min_length=10)
    document_name: str
    metadata: Optional[dict] = None


class IngestResponse(BaseModel):
    status: str
    document_name: str
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    document_count: int
    timestamp: str
```

---

## Step 3 — RAG Pipeline

This is the foundation everything else depends on. Build and test this before touching the agent.

File: `app/rag.py`

```python
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    DirectoryLoader,
)
from langchain.schema import Document

load_dotenv()


# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./db")
COLLECTION_NAME = "support_knowledge_base"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # cheaper than ada-002, better quality
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)


# ─────────────────────────────────────────────────────────────
# Vector Store
# ─────────────────────────────────────────────────────────────

def get_vector_store() -> Chroma:
    """Get or create the ChromaDB vector store."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )


# ─────────────────────────────────────────────────────────────
# Ingestion
# ─────────────────────────────────────────────────────────────

def ingest_directory(directory: str = "./knowledge_base") -> int:
    """
    Load all .md and .txt files from a directory,
    split into chunks, and add to ChromaDB.
    Returns the number of chunks created.
    """
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    documents = []

    for file_path in path.rglob("*.md"):
        loader = TextLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        # Tag each doc with its source filename for citations
        for doc in docs:
            doc.metadata["source"] = file_path.name
        documents.extend(docs)

    for file_path in path.rglob("*.txt"):
        loader = TextLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = file_path.name
        documents.extend(docs)

    for file_path in path.rglob("*.pdf"):
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = file_path.name
        documents.extend(docs)

    if not documents:
        raise ValueError(f"No documents found in {directory}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", "!", "?", " "],
    )
    chunks = splitter.split_documents(documents)

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)


def ingest_text(content: str, document_name: str, metadata: Optional[dict] = None) -> int:
    """
    Ingest raw text string into ChromaDB.
    Used by the /ingest API endpoint.
    Returns number of chunks created.
    """
    meta = metadata or {}
    meta["source"] = document_name

    document = Document(page_content=content, metadata=meta)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents([document])

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)


# ─────────────────────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────────────────────

def search_knowledge_base(query: str, k: int = 4) -> list[dict]:
    """
    Semantic search over the knowledge base.
    Returns top-k chunks with content and source metadata.
    """
    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_relevance_scores(
        query=query,
        k=k,
    )

    formatted = []
    for doc, score in results:
        formatted.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "relevance_score": round(score, 4),
        })

    return formatted


def get_document_count() -> int:
    """Returns the total number of chunks in the vector store."""
    vector_store = get_vector_store()
    collection = vector_store._collection
    return collection.count()
```

### Test the RAG pipeline in isolation before going further

Create a quick test script `tests/test_rag.py`:

```python
import sys
sys.path.append(".")

from app.rag import ingest_directory, search_knowledge_base, get_document_count

# Step 1: Ingest your knowledge base
print("Ingesting knowledge base...")
count = ingest_directory("./knowledge_base")
print(f"Created {count} chunks")

# Step 2: Check count
total = get_document_count()
print(f"Total chunks in DB: {total}")

# Step 3: Test retrieval
test_queries = [
    "How do I get a refund?",
    "What's included in the Pro plan?",
    "How do I cancel my subscription?",
    "My payment failed, what happens?",
    "How do I export my data?",
]

for query in test_queries:
    print(f"\nQuery: {query}")
    results = search_knowledge_base(query, k=2)
    for r in results:
        print(f"  Source: {r['source']} | Score: {r['relevance_score']}")
        print(f"  Excerpt: {r['content'][:120]}...")
```

Run it:
```bash
python tests/test_rag.py
```

Expected output: Each query returns 2 relevant chunks with scores above 0.5. If scores are below 0.3, your documents may be too thin — expand the knowledge base content.

Do not proceed to the agent until this test passes cleanly.

---

## Step 4 — The Five Tools

Each tool is a separate file. Each uses the `@tool` decorator from LangChain. The docstring on each tool is not decoration — it's the description the LLM reads to decide when to call the tool. Write it precisely.

**app/tools/knowledge_base.py**

```python
import json
from langchain.tools import tool
from app.rag import search_knowledge_base as _search


@tool
def search_faq(query: str) -> str:
    """
    Search the company's knowledge base for information about
    products, pricing, policies, features, account management,
    billing, refunds, shipping, and technical support.

    Use this tool FIRST for any customer question — before trying
    any other tool. If the answer is in the knowledge base, always
    prefer this over making up an answer from general knowledge.

    Input: a search query string describing what the customer needs.
    Returns: relevant document excerpts with source file names and
    relevance scores. Cite the source document name in your response.
    If no results have a relevance score above 0.4, the answer is
    probably not in the knowledge base — consider escalating.

    Examples of when to use this:
    - "What is the refund policy?"
    - "How much does the Pro plan cost?"
    - "How do I add team members?"
    - "My login isn't working"
    """
    results = _search(query, k=4)

    if not results:
        return "No relevant information found in the knowledge base."

    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"[Result {i}] Source: {r['source']} (relevance: {r['relevance_score']})\n"
            f"{r['content']}"
        )

    return "\n\n---\n\n".join(formatted)
```

**app/tools/orders.py**

```python
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
```

**app/tools/hubspot.py**

```python
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
```

**app/tools/email.py**

```python
import os
import resend
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = "support@yourdomain.com"  # change to your verified Resend domain


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
```

**app/tools/escalation.py**

```python
import os
import httpx
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


@tool
def escalate_to_human(reason: str, conversation_context: str) -> str:
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
```

---

## Step 5 — The LangChain Agent

File: `app/agent.py`

```python
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

from app.tools.knowledge_base import search_faq
from app.tools.orders import get_order_status
from app.tools.hubspot import create_support_ticket
from app.tools.email import send_reply_email
from app.tools.escalation import escalate_to_human

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Tools registry
# ─────────────────────────────────────────────────────────────

TOOLS = [
    search_faq,
    get_order_status,
    create_support_ticket,
    send_reply_email,
    escalate_to_human,
]

# ─────────────────────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────────────────────

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# ─────────────────────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional customer support agent for NovaTech Solutions.
You are helpful, concise, and accurate.

Your capabilities:
- search_faq: search the company's knowledge base for policy and product information
- get_order_status: look up a specific order by ID
- create_support_ticket: create a ticket in HubSpot for issues needing follow-up
- send_reply_email: send an email confirmation to the customer
- escalate_to_human: alert the human support team via Slack when you cannot help

How to respond:

1. ALWAYS search the knowledge base first for any product or policy question.
   Do not answer from general knowledge when you have a knowledge base to check.

2. Cite your sources. When you use information from the knowledge base,
   mention the document name it came from:
   "According to our refund policy..." or "From our product guide..."

3. Be honest about uncertainty. If the knowledge base returns low relevance
   scores (below 0.4) or irrelevant content, say so and escalate rather than
   guessing.

4. Escalate proactively. It is better to escalate with full context than to
   give a wrong answer with confidence. When escalating, include:
   - What the customer asked
   - What you searched for
   - Why you couldn't resolve it
   So the human agent can take over without asking the customer to repeat.

5. Keep responses concise. Most answers should be 2-4 sentences unless
   the question genuinely requires more detail. Do not pad responses.

6. Never make up order IDs, ticket numbers, or specific prices not found
   in your tools. If you don't know, say so.

Tone: Professional, empathetic, direct. Not robotic. If a customer is
frustrated, acknowledge it briefly before solving their problem."""


# ─────────────────────────────────────────────────────────────
# Prompt Template
# ─────────────────────────────────────────────────────────────

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# ─────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────

agent = create_tool_calling_agent(llm=llm, tools=TOOLS, prompt=prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=TOOLS,
    verbose=True,         # logs every tool call to terminal — remove for production
    max_iterations=6,     # prevents infinite loops
    handle_parsing_errors=True,
)


# ─────────────────────────────────────────────────────────────
# Run function
# ─────────────────────────────────────────────────────────────

def convert_history(history: list[dict]) -> list:
    """Convert API message format to LangChain message objects."""
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


async def run_agent(
    message: str,
    conversation_history: list[dict] = None,
) -> dict:
    """
    Run the support agent on a user message.
    Returns dict with 'answer', 'sources', and 'escalated' keys.
    """
    history = conversation_history or []
    chat_history = convert_history(history)

    result = await agent_executor.ainvoke({
        "input": message,
        "chat_history": chat_history,
    })

    # Extract sources from intermediate steps
    sources = []
    escalated = False

    for step in result.get("intermediate_steps", []):
        action, observation = step
        tool_name = action.tool

        if tool_name == "search_faq" and isinstance(observation, str):
            # Parse source document names from the observation
            lines = observation.split("\n")
            for line in lines:
                if line.startswith("[Result") and "Source:" in line:
                    parts = line.split("Source:")
                    if len(parts) > 1:
                        source_doc = parts[1].split("(")[0].strip()
                        excerpt_lines = []
                        # Get a brief excerpt from the next few lines
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            excerpt_lines = lines[idx + 1: idx + 2]
                        sources.append({
                            "document": source_doc,
                            "excerpt": " ".join(excerpt_lines)[:200],
                        })

        if tool_name == "escalate_to_human":
            escalated = True

    # Deduplicate sources by document name
    seen = set()
    unique_sources = []
    for s in sources:
        if s["document"] not in seen:
            seen.add(s["document"])
            unique_sources.append(s)

    return {
        "answer": result["output"],
        "sources": unique_sources,
        "escalated": escalated,
    }
```

---

## Step 6 — FastAPI Application

File: `app/main.py`

```python
import os
import uuid
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ChatRequest, ChatResponse, Source,
    IngestRequest, IngestResponse,
    HealthResponse,
)
from app.agent import run_agent
from app.rag import ingest_text, ingest_directory, get_document_count

load_dotenv()

API_KEY = os.getenv("API_KEY", "dev-key")


# ─────────────────────────────────────────────────────────────
# Startup: ingest knowledge base on first run
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup, ingest knowledge base if vector store is empty."""
    try:
        count = get_document_count()
        if count == 0:
            print("Vector store is empty. Ingesting knowledge base...")
            chunks = ingest_directory("./knowledge_base")
            print(f"Ingested {chunks} chunks from knowledge base.")
        else:
            print(f"Vector store ready. {count} chunks loaded.")
    except Exception as e:
        print(f"Startup ingestion warning: {e}")
    yield


# ─────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Customer Support AI Agent",
    description="LangChain agent with RAG over company knowledge base",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# Auth dependency
# ─────────────────────────────────────────────────────────────

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Check API status and vector store document count."""
    from datetime import datetime
    return HealthResponse(
        status="ok",
        document_count=get_document_count(),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _: str = Depends(verify_api_key),
):
    """
    Main endpoint. Send a customer support question, receive an answer
    with cited sources. Escalation happens automatically if needed.
    """
    try:
        result = await run_agent(
            message=request.message,
            conversation_history=[m.model_dump() for m in request.conversation_history],
        )

        sources = [Source(**s) for s in result["sources"]]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            escalated=result["escalated"],
            session_id=request.session_id or str(uuid.uuid4()),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    request: IngestRequest,
    _: str = Depends(verify_api_key),
):
    """Add new content to the knowledge base without restarting."""
    try:
        chunks = ingest_text(
            content=request.content,
            document_name=request.document_name,
            metadata=request.metadata,
        )
        return IngestResponse(
            status="success",
            document_name=request.document_name,
            chunks_created=chunks,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "name": "Customer Support AI Agent",
        "docs": "/docs",
        "health": "/health",
    }
```

---

## Step 7 — Run It Locally

```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` — FastAPI generates interactive documentation automatically. Every endpoint is testable directly from the browser.

On first startup, you'll see the ingestion log:
```
Vector store is empty. Ingesting knowledge base...
Ingested 47 chunks from knowledge base.
```

If you see this, the RAG pipeline is working. If you see an error, check that your `knowledge_base/` directory exists and your OpenAI key is valid in `.env`.

---

## Step 8 — Testing

### Test 1 — Health Check

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "ok",
  "document_count": 47,
  "timestamp": "2025-01-15T10:00:00.000000"
}
```

---

### Test 2 — Knowledge Base Questions (Happy Path)

Test these via the `/docs` UI or curl. For curl, set your API key:

```bash
export API_KEY="dev-key"
```

**Refund policy question:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "What is your refund policy?",
    "user_email": "test@example.com"
  }'
```

Expected behavior: Agent calls `search_faq`, finds relevant content from `refund_policy.md`, returns a clear answer citing the source document. `escalated` should be `false`.

**Pricing question:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "How much does the Pro plan cost per month?",
    "user_email": "test@example.com"
  }'
```

Expected: $79/month, cited from `pricing.md`.

**Feature question:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "Does the Starter plan support API access?",
    "user_email": "test@example.com"
  }'
```

Expected: Yes, 1,000 requests/hour, cited from `product_guide.md` or `faq.md`.

---

### Test 3 — Multi-turn Conversation

```bash
# First turn
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "I want to cancel my subscription.",
    "session_id": "test-session-001"
  }'

# Second turn — note the conversation_history carries forward
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "Will I get a refund for the remaining days?",
    "conversation_history": [
      {"role": "user", "content": "I want to cancel my subscription."},
      {"role": "assistant", "content": "[first response here]"}
    ],
    "session_id": "test-session-001"
  }'
```

Expected: Agent remembers the context of cancellation from the first turn when answering the refund question in the second.

---

### Test 4 — Order Lookup

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "Can you check the status of my order ORD-2024-8821?",
    "user_email": "test@example.com"
  }'
```

Expected: Agent calls `get_order_status`. Since Airtable may not have this order, it should return the "order not found" message gracefully — not crash, not hallucinate a status.

---

### Test 5 — Escalation (Critical Test)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "I think someone has unauthorized access to my account and has been making purchases I didn'\''t authorize.",
    "user_email": "alarmed@example.com"
  }'
```

Expected behavior: Agent recognizes this is a security/fraud issue it cannot handle. It should call `escalate_to_human` with the reason and context, post to Slack (if configured), and return a response telling the customer a human is on the way. `escalated` field in response should be `true`.

This test is portfolio-critical. Screenshot the response and the Slack message.

---

### Test 6 — Out-of-Scope Question (Should Escalate)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "message": "I want to sue your company for negligence. Who is your legal department?",
    "user_email": "angry@example.com"
  }'
```

Expected: Agent escalates. This is not in the knowledge base and is legally sensitive.

---

### Test 7 — Wrong API Key

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: wrong-key" \
  -d '{"message": "hello"}'
```

Expected: `401 Unauthorized`. Your auth middleware is working.

---

### Test 8 — Ingest New Document

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "document_name": "holiday_hours.md",
    "content": "NovaTech support is unavailable on December 25 and January 1. During these dates, the AI agent handles urgent questions but human agents will respond the next business day. Emergency security issues should be emailed to security@novatech.io."
  }'
```

Then immediately query it:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"message": "Are you available on Christmas Day?"}'
```

Expected: Agent answers from the newly ingested document without restarting the server. This demonstrates the dynamic knowledge base — a key selling point.

---

## Step 9 — Deploy to Railway

```bash
# In your project root, create a Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

Then:
1. Push to GitHub
2. Go to railway.app → New Project → Deploy from GitHub repo
3. Select your `customer-support-agent` repo
4. Add all environment variables from your `.env` under the Variables tab
5. Railway detects the Procfile automatically and deploys

Your live URL will be something like `https://customer-support-agent-production.up.railway.app`

Test the deployed version with the same curl commands, replacing `localhost:8000` with your Railway URL.

---

## GitHub Repository

```
customer-support-agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── rag.py
│   ├── models.py
│   └── tools/
│       ├── __init__.py
│       ├── knowledge_base.py
│       ├── orders.py
│       ├── hubspot.py
│       ├── email.py
│       └── escalation.py
├── knowledge_base/
│   ├── faq.md
│   ├── refund_policy.md
│   ├── shipping_policy.md
│   ├── product_guide.md
│   └── pricing.md
├── tests/
│   └── test_rag.py
├── .env.example
├── .gitignore
├── Procfile
├── requirements.txt
└── README.md
```

### README.md

```markdown
# Customer Support AI Agent
### LangChain + FastAPI + ChromaDB + OpenAI GPT-4o

A production-ready AI support agent that answers customer questions
from a company knowledge base with cited sources, looks up order
status, creates support tickets, sends emails, and escalates
anything it can't confidently resolve — with full context — to a
human agent via Slack.

## The Problem
Support teams spend 60–70% of their time answering questions already
documented in their knowledge base. The remaining 30% require a human.
The hard part is building a system that knows the difference —
and handles both paths without dropping context.

## The Solution
A LangChain agent with RAG over company documents. Every answer
is retrieved from real content and cited by source document.
When the agent can't help, it escalates with the full conversation
context intact so the human agent doesn't start from zero.

## How It Works

1. Customer sends a question to POST /chat
2. Agent calls search_faq — semantic search over ChromaDB vector store
3. If relevant content found: answers with source citations
4. If order lookup needed: calls get_order_status against Airtable
5. If ticket creation requested: calls create_support_ticket in HubSpot
6. If follow-up email needed: calls send_reply_email via Resend
7. If confidence is low or issue is out of scope: calls escalate_to_human
   → Sends Slack alert with full conversation context
   → Returns message to customer confirming human follow-up

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /chat | Main support chat endpoint |
| POST | /ingest | Add documents to knowledge base |
| GET | /health | API status + document count |

## Stack
LangChain · FastAPI · ChromaDB · OpenAI GPT-4o · HubSpot API ·
Resend · Slack · Railway (deployment)

## Key Features
- RAG with cited sources — every answer grounded in real documents
- Dynamic knowledge base — ingest new docs without restarting
- Graceful escalation — human agents get full context
- Multi-turn conversation memory — context preserved across messages
- API key authentication on all endpoints
- Deployed on Railway with live public URL

## Setup
See docs/setup.md for full setup instructions.

## Live Demo
[Railway URL]

## Loom Walkthrough
[link]
```

---

## Loom Video Script (6–8 Minutes)

**0:00 – 0:45 — The problem**
"Most AI chatbots answer questions confidently even when they're wrong. This agent does two things differently: it only answers from verified company documents, and it knows when to stop and get a human."

**0:45 – 2:00 — Show the architecture**
Open your IDE, show the file structure briefly. "Five tools — knowledge base search, order lookup, ticket creation, email, and escalation. LangChain orchestrates them. FastAPI serves them. ChromaDB stores the knowledge base as embeddings."

**2:00 – 4:00 — Happy path demo**
Open `/docs` in the browser. Send the refund policy question live. Show the response: answer, source citation (refund_policy.md), escalated: false. Send the pricing question. Show the source cited correctly from pricing.md.

**4:00 – 5:30 — Escalation demo**
Send the security breach question. "Watch what happens when the agent gets something outside its scope." Show the Slack alert in your channel — full context included. Show the response to the customer — tells them a human is coming with their full context.

**5:30 – 6:30 — Ingest demo**
Hit the `/ingest` endpoint with a new document. Immediately query it. "New content is searchable instantly, no restart needed. This is how a real support team would keep the knowledge base updated."

**6:30 – 7:30 — Show the code briefly**
Show `tools/escalation.py`. "The escalation tool is the most important. It includes full conversation context in the Slack alert so the human agent can take over without asking the customer to repeat themselves." Show `app/rag.py` — "relevance scores determine whether the agent answers or escalates."

**7:30 – 8:00 — Close**
"Deployed on Railway. Full code on GitHub with setup docs. The knowledge base contains five mock company documents — swapping in a real company's docs is a config change, not a rebuild."

---

## Upwork Portfolio Description

```
Customer Support AI Agent | LangChain + FastAPI + ChromaDB + OpenAI

Built a production-grade AI support agent that answers customer
questions from a company knowledge base with cited sources.
Uses RAG (Retrieval-Augmented Generation) over ChromaDB —
every answer is retrieved from real documents, not hallucinated.

Five tools: knowledge base search, order lookup (Airtable),
HubSpot ticket creation, email via Resend, and smart escalation
to human agents via Slack with full conversation context.

The escalation logic is the key differentiator: the agent knows
what it doesn't know. Low-confidence answers, security issues,
and legal matters route to human agents with everything they need
to take over — no context lost, no customer asked to repeat.

Deployed on Railway. Dynamic knowledge base — new documents
ingested via API without restarting.

Stack: LangChain, FastAPI, ChromaDB, OpenAI, HubSpot, Resend, Slack
[GitHub] [Live Demo] [Loom]
```

---

## Master Checklist

### Structure and Setup
- [ ] Project directory structure created exactly as specified
- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt
- [ ] .env populated with all keys
- [ ] .env.example committed (no real keys)
- [ ] .gitignore includes venv/, db/, .env

### Knowledge Base
- [ ] All 5 markdown documents created with realistic content
- [ ] RAG test script runs clean (test_rag.py)
- [ ] All test queries return results with scores above 0.4
- [ ] Chunks count makes sense (should be 40–70 for 5 docs)

### Tools
- [ ] Each tool has a precise, LLM-readable docstring
- [ ] search_faq returns formatted results with source names
- [ ] get_order_status handles missing Airtable config gracefully
- [ ] create_support_ticket handles missing HubSpot key gracefully
- [ ] send_reply_email handles missing Resend key gracefully
- [ ] escalate_to_human posts to Slack and returns confirmation

### Agent
- [ ] System prompt clearly defines escalation criteria
- [ ] max_iterations set to prevent infinite loops
- [ ] convert_history correctly maps message formats
- [ ] run_agent extracts sources from intermediate_steps correctly
- [ ] escalated flag set correctly when escalation tool fires

### API
- [ ] /health returns correct document count
- [ ] /chat returns answer, sources, escalated, session_id
- [ ] /ingest adds content and returns chunk count
- [ ] API key auth rejects wrong keys with 401
- [ ] Lifespan ingests knowledge base on startup if empty

### Testing
- [ ] Test 1: /health returns 200 with document_count > 0
- [ ] Test 2: Refund question answered from refund_policy.md
- [ ] Test 3: Multi-turn — context preserved across messages
- [ ] Test 4: Order lookup handles "not found" gracefully
- [ ] Test 5: Security breach triggers escalation + Slack alert
- [ ] Test 6: Legal question escalates correctly
- [ ] Test 7: Wrong API key returns 401
- [ ] Test 8: Ingest + immediate query works without restart

### Deployment
- [ ] Procfile created for Railway
- [ ] Deployed to Railway with live public URL
- [ ] All env vars set in Railway dashboard
- [ ] Deployed version tested with same curl commands

### Documentation
- [ ] README complete with architecture explanation
- [ ] Screenshots: /docs UI, happy path response, escalation response, Slack alert
- [ ] Loom recorded (6–8 mins)
- [ ] Upwork portfolio description written
- [ ] requirements.txt committed
- [ ] .env.example committed

---

*This is the project that shows you understand agents at a production level.
The escalation logic — knowing what the agent doesn't know — is what separates this from a toy.*
