"""
RAG isolation test. Run from project root:
    python tests/test_rag.py

Expected output: all 5 queries return chunks with relevance scores above 0.5.
If scores below 0.3 → knowledge base too thin (expand).
If scores 0.3–0.5 → tolerable with MiniLM (lower-dim than OpenAI); proceed but note.
Source guide threshold reference: lines 685–691.
"""

import sys
import os

# Make `app` importable when running this file directly from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag import ingest_directory, search_knowledge_base, get_document_count


def main():
    # Step 1: ingest
    print("Ingesting knowledge base...")
    existing = get_document_count()
    if existing > 0:
        print(f"  Vector store already has {existing} chunks — skipping re-ingest.")
        print(f"  (Delete ./db and re-run if you want a clean ingest.)")
    else:
        count = ingest_directory("./knowledge_base")
        print(f"  Created {count} chunks")

    total = get_document_count()
    print(f"Total chunks in DB: {total}\n")

    # Step 2: test retrieval
    test_queries = [
        "How do I get a refund?",
        "What's included in the Pro plan?",
        "How do I cancel my subscription?",
        "My payment failed, what happens?",
        "How do I export my data?",
    ]

    pass_count = 0
    for query in test_queries:
        print(f"Query: {query}")
        results = search_knowledge_base(query, k=2)
        if not results:
            print("  NO RESULTS\n")
            continue

        top_score = results[0]["relevance_score"]
        for r in results:
            print(
                f"  Source: {r['source']:<22} | Score: {r['relevance_score']:.4f}"
            )
            print(f"  Excerpt: {r['content'][:120].replace(chr(10), ' ')}...")

        if top_score >= 0.5:
            print(f"  ✓ PASS (top score {top_score:.4f} >= 0.5)\n")
            pass_count += 1
        elif top_score >= 0.3:
            print(f"  ~ MARGINAL (top score {top_score:.4f} — acceptable with MiniLM)\n")
            pass_count += 1
        else:
            print(f"  ✗ FAIL (top score {top_score:.4f} < 0.3 — expand knowledge base)\n")

    print(f"Summary: {pass_count}/{len(test_queries)} queries acceptable")


if __name__ == "__main__":
    main()
