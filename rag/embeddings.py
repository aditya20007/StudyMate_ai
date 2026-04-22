import numpy as np
from typing import List
from loguru import logger

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 768

_client = None



def _get_client():
    global _client
    if _client is None:
        from google import genai
        from backend.config import settings
        _client = genai.Client(api_key=settings.google_api_key)
        logger.info(f"Google embedding client ready (model: {EMBEDDING_MODEL})")
    return _client


def embed_texts(texts: List[str], batch_size: int = 100) -> np.ndarray:
    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    client = _get_client()
    all_embeddings = []

    logger.info(f"Embedding {len(texts)} chunks via Google API...")

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
            )
            for emb in result.embeddings:
                all_embeddings.append(emb.values)
        except Exception as e:
            logger.error(f"Google embedding API error on batch {i}: {e}")
            raise RuntimeError(f"Embedding failed: {e}")

    arr = np.array(all_embeddings, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return arr / norms


def embed_query(query: str) -> np.ndarray:
    client = _get_client()
    try:
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
        )
        vec = np.array(result.embeddings[0].values, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
    except Exception as e:
        raise RuntimeError(f"Query embedding failed: {e}")


def get_embedding_dim() -> int:
    return EMBEDDING_DIM

def get_embedding_model():
    return None