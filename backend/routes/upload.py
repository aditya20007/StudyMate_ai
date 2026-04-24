# ============================================================
# backend/routes/upload.py — Upload Endpoints
# ============================================================

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from loguru import logger

from backend.database.session import get_db
from backend.models.db_models import Document
from backend.schemas.schemas import TextUploadRequest, YouTubeUploadRequest, UploadResponse
from backend.services.pdf_service import PDFService
from backend.services.youtube_service import YouTubeService
from rag.pipeline import get_rag_pipeline

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# PDF Upload
# ──────────────────────────────────────────────

@router.post("/pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: int = Form(default=1),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF file, extract text, chunk, and embed into FAISS.
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="PDF exceeds 50MB limit.")

    # Save file temporarily
    temp_path = UPLOAD_DIR / f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract text
        pdf_svc = PDFService()
        raw_text, pdf_meta = PDFService.extract_text(str(temp_path))
        clean_text = PDFService.clean_text(raw_text)

        title = Path(file.filename).stem.replace("_", " ").replace("-", " ").title()

        # Save to DB
        doc = Document(
            user_id=user_id,
            title=title,
            source_type="pdf",
            file_path=str(temp_path),
            word_count=len(clean_text.split()),
            metadata_json=pdf_meta,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Index into RAG pipeline
        pipeline = get_rag_pipeline()
        num_chunks = pipeline.index_document(
            text=clean_text,
            doc_id=doc.id,
            title=title,
            source_type="pdf",
            extra_metadata={"file_name": file.filename, **pdf_meta},
        )

        # Update DB record
        doc.num_chunks = num_chunks
        doc.is_indexed = True
        db.commit()

        logger.info(f"PDF uploaded and indexed: {title} ({num_chunks} chunks)")

        return UploadResponse(
            success=True,
            document_id=doc.id,
            title=title,
            num_chunks=num_chunks,
            word_count=doc.word_count,
            message=f"Successfully processed '{title}' ({num_chunks} chunks created)",
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Note: Keep file for re-processing capability
        pass


# ──────────────────────────────────────────────
# YouTube Upload
# ──────────────────────────────────────────────

@router.post("/youtube", response_model=UploadResponse)
async def upload_youtube(
    request: YouTubeUploadRequest,
    db: Session = Depends(get_db),
):
    """
    Fetch a YouTube video transcript, chunk, and embed into FAISS.
    """
    try:
        yt_svc = YouTubeService()
        transcript, meta = YouTubeService.get_transcript(request.url)

        # Get title
        title = request.title or meta.get("video_title") or YouTubeService.get_video_title(request.url)
        if not title:
            video_id = YouTubeService.extract_video_id(request.url)
            title = f"YouTube Video ({video_id})"

        word_count = len(transcript.split())

        # Save to DB
        doc = Document(
            user_id=request.user_id,
            title=title,
            source_type="youtube",
            source_url=request.url,
            word_count=word_count,
            metadata_json=meta,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Index into RAG
        pipeline = get_rag_pipeline()
        num_chunks = pipeline.index_document(
            text=transcript,
            doc_id=doc.id,
            title=title,
            source_type="youtube",
            extra_metadata={"url": request.url, **meta},
        )

        doc.num_chunks = num_chunks
        doc.is_indexed = True
        db.commit()

        logger.info(f"YouTube indexed: {title} ({num_chunks} chunks)")

        return UploadResponse(
            success=True,
            document_id=doc.id,
            title=title,
            num_chunks=num_chunks,
            word_count=word_count,
            message=f"Successfully fetched and indexed '{title}' ({num_chunks} chunks)",
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube URL: {str(e)}")


# ──────────────────────────────────────────────
# Text Upload
# ──────────────────────────────────────────────

@router.post("/text", response_model=UploadResponse)
async def upload_text(
    request: TextUploadRequest,
    db: Session = Depends(get_db),
):
    """
    Accept raw text notes, chunk, and embed into FAISS.
    """
    try:
        word_count = len(request.content.split())

        if word_count < 20:
            raise HTTPException(
                status_code=422,
                detail="Text is too short. Please provide at least 20 words.",
            )

        # Save to DB
        doc = Document(
            user_id=request.user_id,
            title=request.title,
            source_type="text",
            word_count=word_count,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Index into RAG
        pipeline = get_rag_pipeline()
        num_chunks = pipeline.index_document(
            text=request.content,
            doc_id=doc.id,
            title=request.title,
            source_type="text",
        )

        doc.num_chunks = num_chunks
        doc.is_indexed = True
        db.commit()

        logger.info(f"Text uploaded: '{request.title}' ({num_chunks} chunks)")

        return UploadResponse(
            success=True,
            document_id=doc.id,
            title=request.title,
            num_chunks=num_chunks,
            word_count=word_count,
            message=f"Successfully indexed '{request.title}' ({num_chunks} chunks)",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
