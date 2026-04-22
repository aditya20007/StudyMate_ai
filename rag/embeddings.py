import numpy as np
import requests
from typing import List
from loguru import logger

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 768
API_URL = "https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent"


def _get_api_key():
    from backend.config import settings
    return settings.google_api_key


def embed_texts(texts: List[str], batch_size: int = 100) -> np.ndarray:
    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    api_key = _get_api_key()
    all_embeddings = []
    logger.info(f"Embedding {len(texts)} chunks via Google REST API...")

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        for text in batch:
            try:
                resp = requests.post(
                    f"{API_URL}?key={api_key}",
                    json={
                        "model": f"models/{EMBEDDING_MODEL}",
                        "content": {"parts": [{"text": text}]},
                        "taskType": "RETRIEVAL_DOCUMENT",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                vec = resp.json()["embedding"]["values"]
                all_embeddings.append(vec)
            except Exception as e:
                logger.error(f"Embedding error on chunk {i}: {e}")
                raise RuntimeError(f"Embedding failed: {e}")

    arr = np.array(all_embeddings, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return arr / norms


def embed_query(query: str) -> np.ndarray:
    api_key = _get_api_key()
    try:
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "model": f"models/{EMBEDDING_MODEL}",
                "content": {"parts": [{"text": query}]},
                "taskType": "RETRIEVAL_QUERY",
            },
            timeout=30,
        )
        resp.raise_for_status()
        vec = np.array(resp.json()["embedding"]["values"], dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
    except Exception as e:
        raise RuntimeError(f"Query embedding failed: {e}")


def get_embedding_dim() -> int:
    return EMBEDDING_DIM

def get_embedding_model():
    return None