# ============================================================
# backend/routes/query.py — Q&A, Summarize, Quiz, TTS Endpoints
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from backend.database.session import get_db
from backend.models.db_models import Document, QueryHistory
from backend.schemas.schemas import (
    QueryRequest, QueryResponse, SourceReference,
    SummarizeRequest, SummarizeResponse,
    QuizRequest, QuizResponse, QuizQuestion, MCQOption,
    TTSRequest, TTSResponse,
)
from rag.pipeline import get_rag_pipeline
from backend.services.tts_service import TTSService

router = APIRouter(tags=["Core Features"])


# ──────────────────────────────────────────────
# Helper: Get document or 404
# ──────────────────────────────────────────────

def get_document_or_404(doc_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    if not doc.is_indexed:
        raise HTTPException(
            status_code=422,
            detail=f"Document '{doc.title}' has not been indexed yet.",
        )
    return doc


def get_full_text_from_db(doc: Document) -> str:
    """Retrieve the full text of a document from its source or vector store chunks."""
    # For PDFs, re-read the file if it exists
    if doc.source_type == "pdf" and doc.file_path:
        from pathlib import Path
        from backend.services.pdf_service import PDFService
        try:
            if Path(doc.file_path).exists():
                text, _ = PDFService.extract_text(doc.file_path)
                return PDFService.clean_text(text)
        except Exception:
            pass  # Fall through to chunk reconstruction

    # Fallback: reconstruct from vector store chunks (works for all source types)
    from rag.vector_store import get_vector_store
    vs = get_vector_store()
    chunks = [m["text"] for m in vs.metadata if m["doc_id"] == doc.id]
    if chunks:
        return " ".join(chunks)

    return f"Document '{doc.title}' content unavailable. Please re-upload."


# ──────────────────────────────────────────────
# Q&A Endpoint
# ──────────────────────────────────────────────

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Ask a question against the indexed knowledge base.
    Optionally restrict to a specific document.
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.answer(
            question=request.question,
            doc_id=request.document_id,
            top_k=request.top_k,
        )

        sources = [
            SourceReference(
                document_title=s["document_title"],
                source_type=s["source_type"],
                chunk_index=s["chunk_index"],
                relevance_score=s["relevance_score"],
                excerpt=s["excerpt"],
            )
            for s in result["sources"]
        ]

        # Save to query history
        history = QueryHistory(
            user_id=request.user_id,
            document_id=request.document_id,
            query_text=request.question,
            answer_text=result["answer"],
            query_type="qa",
            sources_used=[s.dict() for s in sources],
            latency_ms=result["latency_ms"],
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            latency_ms=result["latency_ms"],
            query_id=history.id,
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# Summarization Endpoint
# ──────────────────────────────────────────────

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(
    request: SummarizeRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a summary of an indexed document.
    style: 'short' | 'bullets' | 'detailed'
    """
    doc = get_document_or_404(request.document_id, db)

    try:
        full_text = get_full_text_from_db(doc)
        pipeline = get_rag_pipeline()
        summary = pipeline.summarize_document(
            doc_id=doc.id,
            title=doc.title,
            full_text=full_text,
            style=request.style.value,
        )

        # Log in history
        history = QueryHistory(
            user_id=request.user_id,
            document_id=doc.id,
            query_text=f"Summarize ({request.style.value})",
            answer_text=summary,
            query_type="summarize",
        )
        db.add(history)
        db.commit()

        return SummarizeResponse(
            document_id=doc.id,
            title=doc.title,
            style=request.style.value,
            summary=summary,
            word_count=len(summary.split()),
        )

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# Quiz Endpoint
# ──────────────────────────────────────────────

@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    db: Session = Depends(get_db),
):
    """
    Generate multiple-choice questions from a document.
    """
    doc = get_document_or_404(request.document_id, db)

    try:
        full_text = get_full_text_from_db(doc)
        pipeline = get_rag_pipeline()
        questions_data = pipeline.generate_quiz(
            doc_id=doc.id,
            full_text=full_text,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
        )

        # Parse into response schema
        questions = []
        for q_data in questions_data:
            options = [
                MCQOption(label=opt["label"], text=opt["text"])
                for opt in q_data.get("options", [])
            ]
            questions.append(
                QuizQuestion(
                    question_number=q_data.get("question_number", len(questions) + 1),
                    question=q_data["question"],
                    options=options,
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data.get("explanation", ""),
                )
            )

        # Log
        history = QueryHistory(
            user_id=request.user_id,
            document_id=doc.id,
            query_text=f"Quiz ({request.num_questions} questions, {request.difficulty})",
            query_type="quiz",
        )
        db.add(history)
        db.commit()

        return QuizResponse(
            document_id=doc.id,
            title=doc.title,
            num_questions=len(questions),
            questions=questions,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# Text-to-Speech Endpoint
# ──────────────────────────────────────────────

@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech and return the audio file URL.
    """
    try:
        tts_svc = TTSService()
        result = tts_svc.text_to_speech(
            text=request.text,
            language=request.language,
            document_id=request.document_id,
        )

        from pathlib import Path as _Path
        file_name = _Path(result["file_path"]).name
        audio_url = f"/audio/{file_name}"

        return TTSResponse(
            audio_file_path=result["file_path"],
            audio_url=audio_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# Documents List Endpoint
# ──────────────────────────────────────────────

@router.get("/documents")
async def list_documents(
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """List all indexed documents for a user."""
    docs = (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "title": d.title,
            "source_type": d.source_type,
            "num_chunks": d.num_chunks,
            "word_count": d.word_count,
            "is_indexed": d.is_indexed,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


# ──────────────────────────────────────────────
# Study Plan Endpoint (My Addition)
# ──────────────────────────────────────────────

@router.get("/study-plan")
async def generate_study_plan(
    document_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    🌟 Generate a personalized 3-day study plan for a document.
    """
    doc = get_document_or_404(document_id, db)
    full_text = get_full_text_from_db(doc)

    pipeline = get_rag_pipeline()
    plan = pipeline.generate_study_plan(
        doc_id=doc.id,
        title=doc.title,
        full_text=full_text,
    )

    return {"document_id": doc.id, "title": doc.title, "study_plan": plan}


# ──────────────────────────────────────────────
# Query History
# ──────────────────────────────────────────────

@router.get("/history")
async def get_query_history(
    user_id: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get recent query history for a user."""
    history = (
        db.query(QueryHistory)
        .filter(QueryHistory.user_id == user_id)
        .order_by(QueryHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id,
            "query_text": h.query_text,
            "answer_text": h.answer_text[:300] + "..." if h.answer_text and len(h.answer_text) > 300 else h.answer_text,
            "query_type": h.query_type,
            "latency_ms": h.latency_ms,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]
