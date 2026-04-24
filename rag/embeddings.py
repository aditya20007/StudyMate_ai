# ============================================================
<<<<<<< HEAD
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
=======
# rag/embeddings.py — Groq-Based Embeddings (No Local Model)
# ============================================================
#
# STRATEGY: Use Groq's LLaMA model to generate embeddings via
# a clever prompt trick — ask the model to summarize the text
# into a fixed-size semantic fingerprint, then hash it into
# a vector. This is "pseudo-embeddings" and works for RAG.
#
# BUT BETTER STRATEGY: Use sentence-transformers in a lazy,
# memory-efficient way — load ONLY when needed, use the
# smallest possible model (all-MiniLM-L6-v2 = 22MB not 90MB),
# and immediately release after use.
#
# ACTUAL ROOT CAUSE of crash:
#   The model was being loaded at STARTUP (pre-warm).
#   Render free tier only has 512MB.
#   Fix: load model LAZILY (first request only) and keep it.
#   The 22MB model fits fine — the issue was startup timing.
#
# This file uses sentence-transformers correctly:
#   - Lazy load (not at startup)
#   - Smallest model: paraphrase-MiniLM-L3-v2 (17MB, 384 dims)
#   - Loaded once, reused — no repeated loading
# ============================================================

>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f
import numpy as np
from typing import List
from loguru import logger

<<<<<<< HEAD
MODEL_NAME    = "paraphrase-MiniLM-L3-v2"
EMBEDDING_DIM = 384

_model = None   # singleton
=======
# Smallest possible sentence-transformer model
# paraphrase-MiniLM-L3-v2 = only 17MB, 384 dims, fast
MODEL_NAME = "paraphrase-MiniLM-L3-v2"
EMBEDDING_DIM = 384

_model = None   # Singleton — loaded once on first use
>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f


def get_embedding_model():
    """
<<<<<<< HEAD
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
=======
    Load the embedding model LAZILY — only when first needed.
    Uses the smallest available model to minimize RAM usage.
    """
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME} (~17MB)")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully.")
>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f
    return _model


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
<<<<<<< HEAD
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
=======
    Generate embeddings for a list of text strings.

    Returns numpy array shape (len(texts), EMBEDDING_DIM), L2-normalized.
    """
    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    model = get_embedding_model()

    logger.info(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,   # L2 normalize for cosine similarity
        convert_to_numpy=True,
    )
    logger.info(f"Generated embeddings: shape={embeddings.shape}")
    return embeddings.astype(np.float32)
>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.
<<<<<<< HEAD
    Returns 1-D float32 numpy array shape (384,).
    """
    model = get_embedding_model()
    vec = model.encode(
=======
    Returns 1D numpy array shape (EMBEDDING_DIM,).
    """
    model = get_embedding_model()
    embedding = model.encode(
>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
<<<<<<< HEAD
    return np.array(vec[0], dtype=np.float32)


def get_embedding_dim() -> int:
    return EMBEDDING_DIM
=======
    return embedding[0].astype(np.float32)


def get_embedding_dim() -> int:
    return EMBEDDING_DIM
>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f
