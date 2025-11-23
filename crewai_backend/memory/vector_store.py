# ---------------------------------------------------------
# This file manages the ChromaDB vector store:
# - Initializes a persistent collection under db/chroma/
# - Supports adding documents with metadata.
# - Supports semantic search by query string.
# ---------------------------------------------------------
import os
from typing import List, Dict, Any

import chromadb

from .embeddings import embed_texts

# --- This block configures the persistent Chroma client and collection ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "db", "chroma"))
os.makedirs(CHROMA_DIR, exist_ok=True)

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(name="agentic_research_memory")


def add_memory(texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
    """
    Add a batch of texts with associated metadata into the vector store.
    """
    if not texts:
        return

    vectors = embed_texts(texts)
    ids = [f"mem_{i}_{len(vectors)}" for i in range(len(texts))]
    _collection.add(
        embeddings=vectors,
        documents=texts,
        metadatas=metadatas,
        ids=ids,
    )


def search_memory(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for semantically similar items to the query.
    Returns a list of dicts with 'document' and 'metadata'.
    """
    if not query or not query.strip():
        return []

    query_vec = embed_texts([query])[0]
    res = _collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
    )
    results = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        results.append({"document": doc, "metadata": meta})
    return results
