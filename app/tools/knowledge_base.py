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
