# ============================================================
# rag/vector_store.py — FAISS Vector Store (384-dim)
# ============================================================

from __future__ import annotations
import pickle
import numpy as np
import faiss
from pathlib import Path
from typing import List, Optional
from loguru import logger

from backend.config import settings
from rag.embeddings import EMBEDDING_DIM   # 384


class VectorStore:
    """
    Persisted FAISS index with chunk metadata.
    Uses IndexFlatIP (exact cosine search via L2-normalised dot product).
    """

    def __init__(self, store_path: str = None):
        self.store_path = Path(store_path or settings.vector_store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._idx_file  = self.store_path / "faiss_index.bin"
        self._meta_file = self.store_path / "metadata.pkl"
        self.index: Optional[faiss.Index] = None
        self.metadata: List[dict] = []
        self._load_or_create()

    # ── Init ──────────────────────────────────────────────────

    def _create_new(self) -> None:
        self.index    = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.metadata = []
        logger.info(f"New FAISS index created (dim={EMBEDDING_DIM})")

    def _load_or_create(self) -> None:
        if self._idx_file.exists() and self._meta_file.exists():
            try:
                self.index = faiss.read_index(str(self._idx_file))
                with open(self._meta_file, "rb") as fh:
                    self.metadata = pickle.load(fh)
                if self.index.d != EMBEDDING_DIM:
                    logger.warning(
                        f"Dimension mismatch: index={self.index.d}, "
                        f"expected={EMBEDDING_DIM}. Rebuilding."
                    )
                    self._create_new()
                else:
                    logger.info(
                        f"Loaded FAISS index: {self.index.ntotal} vectors, "
                        f"{len(self.metadata)} metadata entries"
                    )
            except Exception as exc:
                logger.error(f"Failed to load index ({exc}). Creating fresh one.")
                self._create_new()
        else:
            self._create_new()

    def _save(self) -> None:
        faiss.write_index(self.index, str(self._idx_file))
        with open(self._meta_file, "wb") as fh:
            pickle.dump(self.metadata, fh)
        logger.info(f"Vector store saved ({self.index.ntotal} vectors)")

    # ── Write ─────────────────────────────────────────────────

    def add_chunks(self, chunks, embeddings: np.ndarray) -> None:
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("chunks / embeddings length mismatch")
        self.index.add(embeddings.astype(np.float32))
        for chunk in chunks:
            self.metadata.append({
                "text":        chunk.text,
                "chunk_index": chunk.chunk_index,
                "doc_id":      chunk.source_doc_id,
                "title":       chunk.source_title,
                "source_type": chunk.source_type,
                "metadata":    chunk.metadata,
                "word_count":  chunk.word_count,
            })
        self._save()
        logger.info(f"Added {len(chunks)} chunks. Total: {self.index.ntotal}")

    # ── Read ──────────────────────────────────────────────────

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        doc_id: Optional[int] = None,
    ) -> List[dict]:
        if self.index.ntotal == 0:
            return []

        q       = query_embedding.astype(np.float32).reshape(1, -1)
        fetch_k = min(top_k * 5 if doc_id else top_k, self.index.ntotal)
        scores, indices = self.index.search(q, fetch_k)

        results: List[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            if doc_id is not None and meta["doc_id"] != doc_id:
                continue
            results.append({
                "text":        meta["text"],
                "score":       float(score),
                "chunk_index": meta["chunk_index"],
                "doc_id":      meta["doc_id"],
                "title":       meta["title"],
                "source_type": meta["source_type"],
                "metadata":    meta.get("metadata", {}),
            })
            if len(results) >= top_k:
                break
        return results

    # ── Properties ────────────────────────────────────────────

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal if self.index else 0

    def get_stats(self) -> dict:
        doc_counts: dict = {}
        for m in self.metadata:
            did = m["doc_id"]
            doc_counts[did] = doc_counts.get(did, 0) + 1
        return {
            "total_vectors":       self.total_vectors,
            "total_documents":     len(doc_counts),
            "embedding_dim":       EMBEDDING_DIM,
            "chunks_per_document": doc_counts,
        }


# ── Singleton ─────────────────────────────────────────────────

_vs: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _vs
    if _vs is None:
        _vs = VectorStore()
    return _vs
