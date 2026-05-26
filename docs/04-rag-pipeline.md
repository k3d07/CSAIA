# 04 — Step 3: RAG Pipeline

Source: lines 486–691 of source file. File: `app/rag.py`.

> **Test this in isolation before touching the agent.** RAG is the foundation. If retrieval doesn't work, nothing downstream works.

## Configuration

```python
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./db")
COLLECTION_NAME = "support_knowledge_base"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",   # cheaper than ada-002, better quality
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)
```

## Vector Store accessor

```python
def get_vector_store() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
```

## Ingestion — Directory

Loads `*.md`, `*.txt`, `*.pdf` from `./knowledge_base`. Tags each doc's metadata with the filename so citations work. Splits with `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ".", "!", "?", " "])`. Returns chunk count.

## Ingestion — Raw Text (for /ingest endpoint)

```python
def ingest_text(content: str, document_name: str, metadata: Optional[dict] = None) -> int:
    meta = metadata or {}
    meta["source"] = document_name
    document = Document(page_content=content, metadata=meta)
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents([document])
    get_vector_store().add_documents(chunks)
    return len(chunks)
```

## Retrieval

```python
def search_knowledge_base(query: str, k: int = 4) -> list[dict]:
    results = get_vector_store().similarity_search_with_relevance_scores(query=query, k=k)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "relevance_score": round(score, 4),
        }
        for doc, score in results
    ]
```

## Doc count helper
```python
def get_document_count() -> int:
    return get_vector_store()._collection.count()
```

## Isolation test — `tests/test_rag.py`

Test queries (5):
1. "How do I get a refund?"
2. "What's included in the Pro plan?"
3. "How do I cancel my subscription?"
4. "My payment failed, what happens?"
5. "How do I export my data?"

**Acceptance:** each query returns 2 relevant chunks with relevance scores **above 0.5**. If scores are **below 0.3**, the knowledge base is too thin — expand it. **Do not proceed to the agent until this passes cleanly.**
