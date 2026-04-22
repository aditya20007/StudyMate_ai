# ============================================================
# rag/vector_store.py — FAISS Vector Store Manager
# ============================================================

import pickle
import numpy as np
import faiss
from pathlib import Path
from typing import List, Optional
from loguru import logger

from backend.config import settings
from rag.embeddings import EMBEDDING_DIM   # 384 (paraphrase-MiniLM-L3-v2)


class VectorStore:
    """
    FAISS-based vector store. Persists to disk between requests.
    """

    def __init__(self, store_path: str = None):
        self.store_path = Path(store_path or settings.vector_store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_path / "faiss_index.bin"
        self.meta_file  = self.store_path / "metadata.pkl"
        self.index: Optional[faiss.Index] = None
        self.metadata: List[dict] = []
        self._load_or_create()

    def _create_new(self):
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.metadata = []
        logger.info(f"Created new FAISS index (dim={EMBEDDING_DIM})")

    def _load_or_create(self):
        if self.index_file.exists() and self.meta_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.meta_file, "rb") as f:
                    self.metadata = pickle.load(f)
                # Rebuild if dim mismatch (e.g. old index from different model)
                if self.index.d != EMBEDDING_DIM:
                    logger.warning(f"Dim mismatch ({self.index.d} vs {EMBEDDING_DIM}). Rebuilding.")
                    self._create_new()
                else:
                    logger.info(f"Loaded FAISS index: {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Load failed: {e}. Creating fresh index.")
                self._create_new()
        else:
            self._create_new()

    def save(self):
        faiss.write_index(self.index, str(self.index_file))
        with open(self.meta_file, "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"Saved vector store ({self.index.ntotal} vectors)")

    def add_chunks(self, chunks, embeddings: np.ndarray):
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("Chunks and embeddings count mismatch.")
        embeddings = embeddings.astype(np.float32)
        self.index.add(embeddings)
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
        self.save()
        logger.info(f"Added {len(chunks)} chunks. Total: {self.index.ntotal}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        doc_id: Optional[int] = None,
    ) -> List[dict]:
        if self.index.ntotal == 0:
            return []
        query   = query_embedding.astype(np.float32).reshape(1, -1)
        fetch_k = min(top_k * 5 if doc_id else top_k, self.index.ntotal)
        scores, indices = self.index.search(query, fetch_k)
        results = []
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


_vector_store_instance = None

def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance