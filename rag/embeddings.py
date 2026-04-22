# ============================================================
# rag/embeddings.py — Groq Embeddings API (Render-Safe)
# ============================================================
#
# WHY THIS CHANGE:
#   sentence-transformers loads a 90MB model into RAM at runtime.
#   Render free tier = 512MB RAM total.
#   FastAPI + SQLAlchemy + FAISS alone use ~300MB.
#   Loading the model pushes it over 512MB → OOM crash → restart loop.
#
# SOLUTION:
#   Use Groq's free embedding API instead.
#   Zero local RAM for the model. Same quality embeddings.
#   Model: nomic-embed-text-v1.5 (768 dims, free on Groq)
# ============================================================

import numpy as np
from typing import List
from loguru import logger
from openai import OpenAI   # Groq is OpenAI-compatible

# ── Embedding config ──────────────────────────────────────────
EMBEDDING_MODEL = "nomic-embed-text-v1.5"
EMBEDDING_DIM = 768   # nomic-embed-text-v1.5 output dimension

_client = None


def _get_client() -> OpenAI:
    """Lazy-load Groq client (OpenAI-compatible)."""
    global _client
    if _client is None:
        from backend.config import settings
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        logger.info(f"Groq embedding client ready (model: {EMBEDDING_MODEL})")
    return _client


def embed_texts(texts: List[str], batch_size: int = 96) -> np.ndarray:
    """
    Generate embeddings for a list of text strings using Groq API.

    Args:
        texts: List of text chunks to embed.
        batch_size: Max texts per API call (Groq limit: 96 per request).

    Returns:
        numpy array of shape (len(texts), EMBEDDING_DIM), L2-normalized.
    """
    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    client = _get_client()
    all_embeddings = []

    logger.info(f"Embedding {len(texts)} chunks via Groq API...")

    # Process in batches to respect API limits
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
                encoding_format="float",
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            logger.error(f"Groq embedding API error on batch {i}: {e}")
            raise RuntimeError(f"Embedding failed: {e}")

    arr = np.array(all_embeddings, dtype=np.float32)

    # L2 normalize for cosine similarity via dot product
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)   # avoid division by zero
    arr = arr / norms

    logger.info(f"Generated embeddings: shape={arr.shape}")
    return arr


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.
    Returns 1D numpy array of shape (EMBEDDING_DIM,).
    """
    result = embed_texts([query])
    return result[0]


def get_embedding_dim() -> int:
    """Return the embedding dimension for the current model."""
    return EMBEDDING_DIM


# Keep this for backward compatibility — not used in Groq version
def get_embedding_model():
    """Not used in Groq version — returns None."""
    return None