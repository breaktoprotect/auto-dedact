from typing import List
import os
import requests


# Default to local TEI, but overridable (same pattern as llm_client)
EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL", "http://localhost:8080/v1/embeddings"
)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-mpnet-base-v2",
)  # embedding model with 768 dimensions


def embed_text(text: str) -> List[float]:
    """
    Generate an embedding vector for the given input text.

    Returns:
        list[float]: embedding vector (768 dims for mpnet)
    """
    text = text.strip()
    if not text:
        raise ValueError("Unexpected value: embed_text() received empty input")

    resp = requests.post(
        EMBEDDING_BASE_URL,
        json={
            "model": EMBEDDING_MODEL,
            "input": [text],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]
