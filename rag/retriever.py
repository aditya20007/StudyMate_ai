# ============================================================
# rag/retriever.py — Retrieval Logic & Re-ranking
# ============================================================

from typing import List, Optional, Tuple
from loguru import logger

from rag.embeddings import embed_query
from rag.vector_store import get_vector_store  


class Retriever:
    """
    Handles retrieval of relevant chunks from the vector store.

    Supports:
    - Basic top-k semantic retrieval
    - Optional MMR (Maximal Marginal Relevance) for diversity
    - Keyword-boosted re-ranking
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
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: The search query string.
            doc_id: If provided, restricts results to this document.
            top_k: Number of results (defaults to self.top_k).
            min_score: Minimum relevance score threshold.

        Returns:
            List of result dicts sorted by relevance score.
        """
        k = top_k or self.top_k

        # Embed the query
        query_embedding = embed_query(query)

        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k * 2,  # Fetch extra for filtering
            doc_id=doc_id,
        )

        # Filter by minimum score
        results = [r for r in results if r["score"] >= min_score]

        # Re-rank with keyword boost
        results = self._keyword_boost(query, results)

        # Return top-k
        return results[:k]

    def retrieve_with_mmr(
        self,
        query: str,
        doc_id: Optional[int] = None,
        top_k: int = 5,
        diversity: float = 0.3,
    ) -> List[dict]:
        """
        Maximal Marginal Relevance retrieval.
        Balances relevance with diversity to avoid redundant chunks.

        Args:
            diversity: 0.0 = pure relevance, 1.0 = pure diversity.
        """
        import numpy as np
        from rag.embeddings import embed_texts

        # Fetch a larger candidate pool
        candidates = self.retrieve(query, doc_id=doc_id, top_k=top_k * 4)

        if not candidates or len(candidates) <= top_k:
            return candidates[:top_k]

        query_embedding = embed_query(query)

        # Embed all candidate chunks
        candidate_texts = [c["text"] for c in candidates]
        candidate_embeddings = embed_texts(candidate_texts)

        selected_indices = []
        remaining_indices = list(range(len(candidates)))

        while len(selected_indices) < top_k and remaining_indices:
            best_idx = None
            best_score = -float("inf")

            for idx in remaining_indices:
                # Relevance to query
                relevance = float(
                    np.dot(query_embedding, candidate_embeddings[idx])
                )

                # Redundancy with already-selected chunks
                if selected_indices:
                    similarities_to_selected = [
                        float(np.dot(candidate_embeddings[idx], candidate_embeddings[s]))
                        for s in selected_indices
                    ]
                    redundancy = max(similarities_to_selected)
                else:
                    redundancy = 0.0

                # MMR score
                mmr_score = (1 - diversity) * relevance - diversity * redundancy

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)

        return [candidates[i] for i in selected_indices]

    @staticmethod
    def _keyword_boost(query: str, results: List[dict], boost: float = 0.05) -> List[dict]:
        """
        Boost scores for results containing query keywords.
        Simple but effective re-ranking on top of semantic search.
        """
        import re

        # Extract meaningful keywords (ignore stopwords)
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "have", "has", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "what", "how", "why", "when",
            "where", "who", "which", "that", "this", "these", "those", "in",
            "on", "at", "to", "for", "of", "and", "or", "but", "not",
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
        """
        Format retrieved chunks into a single context string for the LLM.
        Includes source attribution.
        """
        parts = []
        total_chars = 0

        for i, result in enumerate(results, 1):
            header = f"[Source {i}: {result['title']} ({result['source_type'].upper()})]"
            body = result["text"]
            chunk = f"{header}\n{body}"

            if total_chars + len(chunk) > max_chars:
                # Truncate the last chunk to fit
                remaining = max_chars - total_chars
                if remaining > 200:
                    parts.append(chunk[:remaining] + "...")
                break

            parts.append(chunk)
            total_chars += len(chunk)

        return "\n\n---\n\n".join(parts)
