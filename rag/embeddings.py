# ============================================================
# rag/embeddings.py — Sentence Transformer Embeddings
# ============================================================

import numpy as np
from typing import List, Union
from loguru import logger
from sentence_transformers import SentenceTransformer

# Singleton model instance — load once, reuse everywhere
_model_instance = None
MODEL_NAME = "all-MiniLM-L6-v2"   # Fast, 384-dim, great for semantic search


def get_embedding_model() -> SentenceTransformer:
    """
    Load the sentence transformer model (singleton pattern).
    Downloads ~90MB on first run, then cached locally.
    """
    global _model_instance
    if _model_instance is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model_instance = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully.")
    return _model_instance


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of text chunks to embed.
        batch_size: Number of texts to embed at once.

    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    model = get_embedding_model()

    logger.info(f"Embedding {len(texts)} chunks (batch_size={batch_size})...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 10,
        normalize_embeddings=True,  # L2 normalize for cosine similarity
        convert_to_numpy=True,
    )
    logger.info(f"Generated embeddings: shape={embeddings.shape}")
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.
    Returns 1D numpy array.
    """
    model = get_embedding_model()
    embedding = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embedding[0]  # Return 1D array


def get_embedding_dim() -> int:
    """Return the embedding dimension for the loaded model."""
    model = get_embedding_model()
    return model.get_sentence_embedding_dimension()
