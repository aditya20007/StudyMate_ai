# ============================================================
# rag/retriever.py - Retrieval with keyword boost
# ============================================================

import re
import numpy as np
from typing import List, Optional
from loguru import logger

from rag.embeddings import embed_query, embed_texts
from rag.vector_store import get_vector_store


class Retriever:
    """
    Handles retrieval of relevant chunks from the vector store.
    Uses Groq API for embeddings - no local model needed.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.vector_store = get_vector_store()

    def retrieve(
        self,
        query: str,
        doc_id: Optional[int] = None,
        top_k: Optional[int] = None,
        min_score: float = 0.0,
    ) -> List[dict]:
        k = top_k or self.top_k
        query_embedding = embed_query(query)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k * 2,
            doc_id=doc_id,
        )
        results = [r for r in results if r["score"] >= min_score]
        results = self._keyword_boost(query, results)
        return results[:k]

    @staticmethod
    def _keyword_boost(query: str, results: List[dict], boost: float = 0.05) -> List[dict]:
        stopwords = {
            "a","an","the","is","are","was","were","be","been","have","has","do",
            "does","did","will","would","could","should","may","might","can",
            "what","how","why","when","where","who","which","that","this",
            "these","those","in","on","at","to","for","of","and","or","but","not",
        }
        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        if not keywords:
            return results

        for result in results:
            text_lower = result["text"].lower()
            keyword_hits = sum(1 for kw in keywords if kw in text_lower)
            keyword_ratio = keyword_hits / len(keywords)
            result["score"] = result["score"] + (keyword_ratio * boost)

        return sorted(results, key=lambda r: r["score"], reverse=True)

    def get_context_string(self, results: List[dict], max_chars: int = 6000) -> str:
        parts = []
        total_chars = 0
        for i, result in enumerate(results, 1):
            header = f"[Source {i}: {result['title']} ({result['source_type'].upper()})]"
            body = result["text"]
            chunk = f"{header}\n{body}"
            if total_chars + len(chunk) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 200:
                    parts.append(chunk[:remaining] + "...")
                break
            parts.append(chunk)
            total_chars += len(chunk)
        return "\n\n---\n\n".join(parts)