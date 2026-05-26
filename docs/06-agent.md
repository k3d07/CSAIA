# 06 — Step 5: LangChain Agent

Source: lines 1023–1209 of source file. File: `app/agent.py`.

## Tools Registry
```python
TOOLS = [search_faq, get_order_status, create_support_ticket, send_reply_email, escalate_to_human]
```

## LLM
```python
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
```

## System Prompt (verbatim from source)

Identity: "You are a professional customer support agent for NovaTech Solutions. You are helpful, concise, and accurate."

Six rules:
1. ALWAYS search the knowledge base first. Don't answer from general knowledge.
2. Cite sources. ("According to our refund policy..." / "From our product guide...")
3. Be honest about uncertainty. If scores < 0.4 or irrelevant content, escalate rather than guess.
4. Escalate proactively with: what was asked, what you searched for, why you couldn't resolve. Don't make humans ask the customer to repeat.
5. Keep responses concise — 2–4 sentences unless the question requires more.
6. Never make up order IDs, ticket numbers, or specific prices.

Tone: Professional, empathetic, direct. Not robotic. Acknowledge frustration briefly before solving.

## Prompt Template

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
```

## Agent Executor

```python
agent = create_tool_calling_agent(llm=llm, tools=TOOLS, prompt=prompt)
agent_executor = AgentExecutor(
    agent=agent, tools=TOOLS,
    verbose=True,         # remove for production
    max_iterations=6,     # prevents infinite loops
    handle_parsing_errors=True,
)
```

## convert_history

Maps `[{role, content}]` → `[HumanMessage / AIMessage]`. Only `"user"` and `"assistant"` roles handled.

## run_agent — Source Extraction Logic

After `await agent_executor.ainvoke({"input": message, "chat_history": chat_history})`:

1. Iterate `result["intermediate_steps"]` — each is `(AgentAction, observation)`.
2. If `tool_name == "search_faq"`: parse `[Result N] Source: <file>` lines from observation. Capture next line as excerpt (cap 200 chars).
3. If `tool_name == "escalate_to_human"`: set `escalated = True`.
4. Deduplicate sources by document name.

Return: `{"answer": result["output"], "sources": unique_sources, "escalated": escalated}`.

## Why intermediate_steps?
Because the LLM's final answer is text; we need structured citations. We parse tool observations to reconstruct what was retrieved. Brittle but works — alternative is a custom callback that records tool calls.
