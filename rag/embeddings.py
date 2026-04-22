# ============================================================
# rag/embeddings.py — Google Generative AI Embeddings (Free)
# ============================================================
#
# WHY GOOGLE EMBEDDINGS:
#   - Groq has NO embedding models (confirmed April 2025)
#   - Google Generative AI offers FREE embeddings
#   - Model: text-embedding-004 (768 dims, free tier)
#   - 1500 requests/minute free, no credit card needed
#   - Zero RAM — all computation happens on Google's servers
#
# SETUP: Get free API key at https://aistudio.google.com/apikey
# Add GOOGLE_API_KEY to Render environment variables
# ============================================================

import numpy as np
from typing import List
from loguru import logger

EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIM = 768

_client = None


def _get_client():
    """Lazy-load Google Generative AI client."""
    global _client
    if _client is None:
        import google.generativeai as genai
        from backend.config import settings
        genai.configure(api_key=settings.google_api_key)
        _client = genai
        logger.info(f"Google embedding client ready (model: {EMBEDDING_MODEL})")
    return _client


def embed_texts(texts: List[str], batch_size: int = 100) -> np.ndarray:
    """
    Generate embeddings using Google's free text-embedding-004 model.

    Args:
        texts: List of text chunks to embed.
        batch_size: Max texts per API call.

    Returns:
        numpy array shape (len(texts), 768), L2-normalized.
    """
    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    genai = _get_client()
    all_embeddings = []

    logger.info(f"Embedding {len(texts)} chunks via Google API...")

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=batch,
                task_type="retrieval_document",
            )
            embeddings = result["embedding"]
            # embed_content returns a list when given a list
            if isinstance(embeddings[0], float):
                # single item returned as flat list
                all_embeddings.append(embeddings)
            else:
                all_embeddings.extend(embeddings)
        except Exception as e:
            logger.error(f"Google embedding API error on batch {i}: {e}")
            raise RuntimeError(f"Embedding failed: {e}")

    arr = np.array(all_embeddings, dtype=np.float32)

    # L2 normalize for cosine similarity
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    arr = arr / norms

    logger.info(f"Generated embeddings: shape={arr.shape}")
    return arr


def embed_query(query: str) -> np.ndarray:
    """Embed a single query. Returns 1D array shape (768,)."""
    genai = _get_client()
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query",
        )
        vec = np.array(result["embedding"], dtype=np.float32)
        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
    except Exception as e:
        raise RuntimeError(f"Query embedding failed: {e}")


def get_embedding_dim() -> int:
    return EMBEDDING_DIM


def get_embedding_model():
    """Not used — returns None for compatibility."""
    return None