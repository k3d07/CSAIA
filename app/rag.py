import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.schema import Document

load_dotenv()


# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./db")
COLLECTION_NAME = "support_knowledge_base"
FASTEMBED_CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", "./model_cache")


class LocalFastEmbeddings(Embeddings):
    """Direct fastembed wrapper — bypasses langchain_community's broken PrivateAttr init."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", cache_dir: str = "./model_cache"):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        list(self._model.embed(["warmup"]))  # trigger model load now, not on first query

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(e) for e in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(self._model.embed([text]))[0]


embeddings = LocalFastEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    cache_dir=FASTEMBED_CACHE_DIR,
)


# ─────────────────────────────────────────────────────────────
# Vector Store
# ─────────────────────────────────────────────────────────────

def get_vector_store() -> Chroma:
    """Get or create the ChromaDB vector store.

    `collection_metadata={"hnsw:space": "cosine"}` forces Chroma to use cosine
    distance instead of the default L2. Required for sentence-transformer
    embeddings — without it, similarity_search_with_relevance_scores returns
    out-of-range values (including negatives).
    """
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )


# ─────────────────────────────────────────────────────────────
# Ingestion
# ─────────────────────────────────────────────────────────────

def ingest_directory(directory: str = "./knowledge_base") -> int:
    """
    Load all .md, .txt, and .pdf files from a directory,
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


def ingest_text(
    content: str, document_name: str, metadata: Optional[dict] = None
) -> int:
    """
    Ingest raw text string into ChromaDB. Used by the /ingest API endpoint.
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
