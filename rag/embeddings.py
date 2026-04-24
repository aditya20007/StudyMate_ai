# ============================================================
# rag/embeddings.py — Lazy Sentence-Transformer Embeddings
# ============================================================
#
# Model: paraphrase-MiniLM-L3-v2
#   Size:       17MB  (vs 90MB for all-MiniLM-L6-v2)
#   Dimensions: 384
#   Quality:    Good for RAG semantic search
#   RAM usage:  ~40MB when loaded
#
# Loading strategy:
#   - Model is NOT imported at module level
#   - torch/sentence_transformers imported inside the function
#   - This means: zero extra RAM at server startup
#   - On first upload: model downloads (~17MB) and loads
#   - Every call after that: instant (model stays in memory)
# ============================================================

from __future__ import annotations
import numpy as np
from typing import List
from loguru import logger

MODEL_NAME    = "paraphrase-MiniLM-L3-v2"
EMBEDDING_DIM = 384

_model = None   # singleton


def get_embedding_model():
    """
    Load the SentenceTransformer model on first call only.
    torch and sentence_transformers are imported here (not at module top)
    so they don't consume RAM until actually needed.
    """
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        from sentence_transformers import SentenceTransformer   # lazy import
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded and cached.")
    return _model


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Embed a list of text strings.
    Returns float32 numpy array shape (N, 384), L2-normalised.
    """
    if not texts:
        raise ValueError("Cannot embed an empty list.")

    model = get_embedding_model()
    logger.info(f"Embedding {len(texts)} chunks...")

    vecs = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    arr = np.array(vecs, dtype=np.float32)
    logger.info(f"Embeddings done: shape={arr.shape}")
    return arr


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.
    Returns 1-D float32 numpy array shape (384,).
    """
    model = get_embedding_model()
    vec = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.array(vec[0], dtype=np.float32)


def get_embedding_dim() -> int:
    return EMBEDDING_DIM
