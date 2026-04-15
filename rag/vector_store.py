# ============================================================
# rag/vector_store.py — FAISS Vector Store Manager
# ============================================================

import os
import json
import pickle
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger

from backend.config import settings
from rag.embeddings import get_embedding_dim


class VectorStore:
    """
    FAISS-based vector store for semantic similarity search.
    
    Persists the index and metadata to disk so data survives restarts.
    
    Structure:
    - faiss_index.bin  → The FAISS index (embeddings)
    - metadata.pkl     → Chunk metadata (text, doc info, etc.)
    """

    def __init__(self, store_path: str = None):
        self.store_path = Path(store_path or settings.vector_store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.index_file = self.store_path / "faiss_index.bin"
        self.meta_file = self.store_path / "metadata.pkl"

        self.index: Optional[faiss.Index] = None
        self.metadata: List[dict] = []  # Parallel list to FAISS vectors

        self._load_or_create()

    # ──────────────────────────────────────────────
    # Initialization
    # ──────────────────────────────────────────────

    def _load_or_create(self):
        """Load existing index from disk or create a fresh one."""
        if self.index_file.exists() and self.meta_file.exists():
            self._load()
        else:
            self._create_new()

    def _create_new(self):
        """Create a new FAISS index."""
        dim = get_embedding_dim()
        # IndexFlatIP = Inner Product (cosine similarity when normalized)
        self.index = faiss.IndexFlatIP(dim)
        self.metadata = []
        logger.info(f"Created new FAISS index (dim={dim})")

    def _load(self):
        """Load index and metadata from disk."""
        try:
            self.index = faiss.read_index(str(self.index_file))
            with open(self.meta_file, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(
                f"Loaded FAISS index: {self.index.ntotal} vectors, "
                f"{len(self.metadata)} metadata entries"
            )
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}. Creating fresh index.")
            self._create_new()

    def save(self):
        """Persist the index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_file))
        with open(self.meta_file, "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"Saved vector store ({self.index.ntotal} vectors)")

    # ──────────────────────────────────────────────
    # Indexing
    # ──────────────────────────────────────────────

    def add_chunks(self, chunks, embeddings: np.ndarray):
        """
        Add text chunks and their embeddings to the store.

        Args:
            chunks: List of TextChunk objects.
            embeddings: numpy array (n_chunks, dim), L2-normalized.
        """
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("Mismatch: chunks and embeddings must have same length.")

        # FAISS requires float32
        embeddings = embeddings.astype(np.float32)
        self.index.add(embeddings)

        # Store metadata for each chunk
        for chunk in chunks:
            self.metadata.append({
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "doc_id": chunk.source_doc_id,
                "title": chunk.source_title,
                "source_type": chunk.source_type,
                "metadata": chunk.metadata,
                "word_count": chunk.word_count,
            })

        self.save()
        logger.info(f"Added {len(chunks)} chunks. Total: {self.index.ntotal}")

    def delete_document_chunks(self, doc_id: int):
        """
        Remove all chunks belonging to a document.
        Note: FAISS doesn't support deletion natively — we rebuild.
        """
        # Find indices to keep
        keep_indices = [
            i for i, m in enumerate(self.metadata) if m["doc_id"] != doc_id
        ]

        if len(keep_indices) == len(self.metadata):
            logger.warning(f"No chunks found for doc_id={doc_id}")
            return

        removed = len(self.metadata) - len(keep_indices)
        logger.info(f"Removing {removed} chunks for doc_id={doc_id}")

        # Reconstruct index from kept vectors
        dim = self.index.d
        kept_vectors = faiss.rev_swig_ptr(self.index.get_xb(), self.index.ntotal * dim)
        kept_vectors = np.array(kept_vectors).reshape(self.index.ntotal, dim)
        kept_vectors = kept_vectors[keep_indices]

        new_index = faiss.IndexFlatIP(dim)
        if len(kept_vectors) > 0:
            new_index.add(kept_vectors.astype(np.float32))

        self.index = new_index
        self.metadata = [self.metadata[i] for i in keep_indices]
        self.save()

    # ──────────────────────────────────────────────
    # Retrieval
    # ──────────────────────────────────────────────

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        doc_id: Optional[int] = None,
    ) -> List[dict]:
        """
        Find the most similar chunks to a query embedding.

        Args:
            query_embedding: 1D float32 array.
            top_k: Number of results to return.
            doc_id: If set, restrict search to this document.

        Returns:
            List of dicts with 'text', 'score', and metadata.
        """
        if self.index.ntotal == 0:
            return []

        query = query_embedding.astype(np.float32).reshape(1, -1)

        # Retrieve more than needed if filtering by doc_id
        fetch_k = top_k * 5 if doc_id else top_k
        fetch_k = min(fetch_k, self.index.ntotal)

        scores, indices = self.index.search(query, fetch_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]

            # Filter by document if requested
            if doc_id is not None and meta["doc_id"] != doc_id:
                continue

            results.append({
                "text": meta["text"],
                "score": float(score),
                "chunk_index": meta["chunk_index"],
                "doc_id": meta["doc_id"],
                "title": meta["title"],
                "source_type": meta["source_type"],
                "metadata": meta.get("metadata", {}),
            })

            if len(results) >= top_k:
                break

        return results

    # ──────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal if self.index else 0

    def get_document_chunk_count(self, doc_id: int) -> int:
        """Count how many chunks belong to a document."""
        return sum(1 for m in self.metadata if m["doc_id"] == doc_id)

    def get_stats(self) -> dict:
        """Return store statistics."""
        doc_counts = {}
        for m in self.metadata:
            did = m["doc_id"]
            doc_counts[did] = doc_counts.get(did, 0) + 1

        return {
            "total_vectors": self.total_vectors,
            "total_documents": len(doc_counts),
            "chunks_per_document": doc_counts,
        }


# --- Singleton ---
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get or create the global VectorStore instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
