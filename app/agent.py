import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate

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
# Using ReAct agent to bypass Groq's tool-call API validation entirely.
# Models like llama-3.3-70b-versatile emit XML-format tool calls which
# Groq's API rejects. ReAct uses text-based action parsing — no tool API.
# ─────────────────────────────────────────────────────────────

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

# ─────────────────────────────────────────────────────────────
# ReAct Prompt Template
# Required variables: {tools}, {tool_names}, {input},
#                     {agent_scratchpad}, {chat_history}
# ─────────────────────────────────────────────────────────────

REACT_TEMPLATE = """You are a professional customer support agent for NovaTech Solutions.
You are helpful, concise, and accurate.

Guidelines:
- ALWAYS search the knowledge base first for any product or policy question.
- Cite your sources: "According to our refund policy..." or "From our product guide..."
- If knowledge base relevance scores are below 0.4 or results are irrelevant, escalate instead of guessing.
- When escalating, include what the customer asked, what you searched, and why you couldn't resolve it.
- Keep responses to 2-4 sentences unless more detail is genuinely needed.
- Never invent order IDs, ticket numbers, or prices not found in your tools.
- Tone: professional, empathetic, direct.

You have access to the following tools:

{tools}

STRICT FORMAT RULES — follow this EXACTLY every time:

Question: the input question you must answer
Thought: think about what to do next
Action: one of [{tool_names}]
Action Input: the input string for the tool
Observation: the result of the tool
(you may repeat Thought/Action/Action Input/Observation if you need another tool)
Thought: I now know the final answer
Final Answer: your complete response to the customer

CRITICAL RULES:
- After an Observation, if you have enough information, IMMEDIATELY write "Thought: I now know the final answer" then "Final Answer: ..."
- NEVER write "Action: None" or "Action: N/A" — if you are done with tools, go straight to Final Answer.
- Action MUST always be one of the exact tool names: {tool_names}

Previous conversation:
{chat_history}

Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(REACT_TEMPLATE)

# ─────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────

agent = create_react_agent(llm=llm, tools=TOOLS, prompt=prompt)

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

def convert_history(history: list[dict]) -> str:
    """Convert API message list to a plain-text string for the ReAct prompt."""
    if not history:
        return "None"
    lines = []
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Agent"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


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
