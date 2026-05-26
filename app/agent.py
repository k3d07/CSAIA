import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
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
# LLM — Groq (swapped from OpenAI gpt-4o for free-tier compliance)
# ─────────────────────────────────────────────────────────────

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
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
    return_intermediate_steps=True,
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
