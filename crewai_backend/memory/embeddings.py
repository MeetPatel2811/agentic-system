# ---------------------------------------------------------
# This file wraps the OpenAI embeddings API.
# - Uses text-embedding-3-small to encode text into vectors.
# - Used by the vector store for semantic memory.
# ---------------------------------------------------------
from typing import List
from openai import OpenAI

# --- This block creates a reusable OpenAI client ---
_client = OpenAI()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts into vector representations using
    OpenAI's text-embedding-3-small model.

    Requires the OPENAI_API_KEY environment variable to be set.
    """
    if not texts:
        return []

    response = _client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]
