# ---------------------------------------------------------
# This file exposes a vector memory retrieval tool.
# - Agents can use it to recall semantically related past info.
# - Under the hood it uses ChromaDB + OpenAI embeddings.
# ---------------------------------------------------------
from crewai.tools import tool
from typing import List

from memory.vector_store import search_memory


@tool("Vector Memory Retrieve Tool")
def vector_memory_retrieve_tool(query: str) -> str:
    """
    Retrieve semantically similar past memory entries for a given query.
    Returns a text listing of past documents and their metadata.
    """
    results = search_memory(query, top_k=5)
    if not results:
        return "No related memory found."

    lines: List[str] = ["Related memory entries:"]
    for i, r in enumerate(results, 1):
        doc = r.get("document", "")
        meta = r.get("metadata", {})
        source = meta.get("source", "unknown")
        lines.append(f"{i}. [source={source}] {doc}")
    return "\n".join(lines)
