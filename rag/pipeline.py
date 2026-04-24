# ============================================================
# rag/pipeline.py — Full RAG Pipeline Orchestrator
# ============================================================

import time
from typing import List, Optional, Tuple
from loguru import logger

from backend.config import settings
from backend.utils.chunker import TextChunker, TextChunk
from rag.embeddings import embed_texts, embed_query
from rag.vector_store import get_vector_store
from backend.services.llm_service import LLMService


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline.
    
    Orchestrates:
    1. Indexing: Text → Chunks → Embeddings → FAISS
    2. Retrieval: Query → Embedding → Top-K Chunks
    3. Generation: Chunks + Query → LLM → Answer
    """

    def __init__(self):
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.vector_store = get_vector_store()
        self.llm = LLMService()

    # ──────────────────────────────────────────────
    # Indexing
    # ──────────────────────────────────────────────

    def index_document(
        self,
        text: str,
        doc_id: int,
        title: str,
        source_type: str,
        extra_metadata: dict = None,
    ) -> int:
        """
        Process and index a document into the vector store.

        Returns:
            Number of chunks created.
        """
        logger.info(f"Indexing document: '{title}' (id={doc_id})")

        # Step 1: Chunk the text
        chunks = self.chunker.chunk_text(
            text=text,
            doc_id=doc_id,
            title=title,
            source_type=source_type,
            extra_metadata=extra_metadata or {},
        )

        if not chunks:
            raise ValueError("No chunks were created from the document.")

        # Step 2: Generate embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = embed_texts(chunk_texts)

        # Step 3: Store in FAISS
        self.vector_store.add_chunks(chunks, embeddings)

        logger.info(f"Indexed {len(chunks)} chunks for '{title}'")
        return len(chunks)

    # ──────────────────────────────────────────────
    # Retrieval
    # ──────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        doc_id: Optional[int] = None,
    ) -> List[dict]:
        """
        Retrieve the most relevant chunks for a query.

        Returns:
            List of result dicts with text and metadata.
        """
        top_k = top_k or settings.top_k_results
        query_embedding = embed_query(query)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            doc_id=doc_id,
        )

        logger.debug(f"Retrieved {len(results)} chunks for query: '{query[:80]}...'")
        return results

    # ──────────────────────────────────────────────
    # Q&A
    # ──────────────────────────────────────────────

    def answer(
        self,
        question: str,
        doc_id: Optional[int] = None,
        top_k: int = None,
    ) -> dict:
        """
        Full RAG Q&A: retrieve context → generate answer.

        Returns:
            dict with 'answer', 'sources', 'latency_ms'
        """
        start = time.time()

        # Step 1: Retrieve relevant chunks
        results = self.retrieve(question, top_k=top_k, doc_id=doc_id)

        if not results:
            return {
                "answer": (
                    "I couldn't find any relevant information in your uploaded materials. "
                    "Please upload some content first using the sidebar."
                ),
                "sources": [],
                "latency_ms": int((time.time() - start) * 1000),
            }

        # Step 2: Format context for LLM
        context_chunks = [r["text"] for r in results]

        # Step 3: Generate answer
        answer = self.llm.answer_question(question, context_chunks)

        # Step 4: Build source references
        sources = []
        for r in results:
            sources.append({
                "document_title": r["title"],
                "source_type": r["source_type"],
                "chunk_index": r["chunk_index"],
                "relevance_score": round(r["score"], 4),
                "excerpt": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
            })

        latency_ms = int((time.time() - start) * 1000)
        logger.info(f"Q&A completed in {latency_ms}ms")

        return {
            "answer": answer,
            "sources": sources,
            "latency_ms": latency_ms,
        }

    # ──────────────────────────────────────────────
    # Summarization
    # ──────────────────────────────────────────────

    def summarize_document(
        self,
        doc_id: int,
        title: str,
        full_text: str,
        style: str = "bullets",
    ) -> str:
        """
        Summarize a document.
        Uses the full text (truncated) for better coverage.
        """
        logger.info(f"Summarizing doc_id={doc_id}, style={style}")
        return self.llm.summarize(full_text, style=style, title=title)

    # ──────────────────────────────────────────────
    # Quiz
    # ──────────────────────────────────────────────

    def generate_quiz(
        self,
        doc_id: int,
        full_text: str,
        num_questions: int = 5,
        difficulty: str = "medium",
    ) -> List[dict]:
        """Generate quiz questions from document content."""
        logger.info(f"Generating {num_questions} quiz questions for doc_id={doc_id}")
        return self.llm.generate_quiz(full_text, num_questions, difficulty)

    # ──────────────────────────────────────────────
    # Study Plan (My Addition)
    # ──────────────────────────────────────────────

    def generate_study_plan(self, doc_id: int, title: str, full_text: str) -> str:
        """Generate a personalized study plan for a document."""
        # First summarize, then build plan
        summary = self.llm.summarize(full_text, style="bullets", title=title)
        return self.llm.generate_study_plan(summary, title)


# --- Singleton ---
_pipeline_instance = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the global RAGPipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
