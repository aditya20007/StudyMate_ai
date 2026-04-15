# ============================================================
# backend/schemas/schemas.py — Pydantic Request/Response Models
# ============================================================

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class SourceType(str, Enum):
    PDF = "pdf"
    YOUTUBE = "youtube"
    TEXT = "text"


class SummaryStyle(str, Enum):
    SHORT = "short"
    BULLETS = "bullets"
    DETAILED = "detailed"


class QueryType(str, Enum):
    QA = "qa"
    SUMMARIZE = "summarize"
    QUIZ = "quiz"


# ──────────────────────────────────────────────
# Upload Schemas
# ──────────────────────────────────────────────

class TextUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300, description="Title for this note")
    content: str = Field(..., min_length=10, description="Raw text content")
    user_id: Optional[int] = Field(default=1, description="User ID (defaults to guest)")

    @validator("content")
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only.")
        return v.strip()


class YouTubeUploadRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    title: Optional[str] = Field(default=None, description="Custom title (auto-detected if omitted)")
    user_id: Optional[int] = Field(default=1)

    @validator("url")
    def validate_youtube_url(cls, v):
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("URL must be a valid YouTube link.")
        return v


# ──────────────────────────────────────────────
# Query Schemas
# ──────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Question to ask the knowledge base")
    document_id: Optional[int] = Field(default=None, description="Limit search to one document")
    user_id: Optional[int] = Field(default=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceReference(BaseModel):
    document_title: str
    source_type: str
    chunk_index: int
    relevance_score: float
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    latency_ms: int
    query_id: Optional[int] = None


# ──────────────────────────────────────────────
# Summarization Schemas
# ──────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to summarize")
    style: SummaryStyle = Field(default=SummaryStyle.BULLETS)
    user_id: Optional[int] = Field(default=1)


class SummarizeResponse(BaseModel):
    document_id: int
    title: str
    style: str
    summary: str
    word_count: int


# ──────────────────────────────────────────────
# Quiz Schemas
# ──────────────────────────────────────────────

class MCQOption(BaseModel):
    label: str       # A, B, C, D
    text: str


class QuizQuestion(BaseModel):
    question_number: int
    question: str
    options: List[MCQOption]
    correct_answer: str   # A, B, C, or D
    explanation: str


class QuizRequest(BaseModel):
    document_id: int
    num_questions: int = Field(default=5, ge=3, le=10)
    user_id: Optional[int] = Field(default=1)
    difficulty: str = Field(default="medium")  # easy | medium | hard


class QuizResponse(BaseModel):
    document_id: int
    title: str
    num_questions: int
    questions: List[QuizQuestion]


# ──────────────────────────────────────────────
# TTS Schemas
# ──────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=5000)
    document_id: Optional[int] = None
    language: str = Field(default="en")


class TTSResponse(BaseModel):
    audio_file_path: str
    audio_url: str
    duration_hint: Optional[float] = None


# ──────────────────────────────────────────────
# Document Schemas
# ──────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    title: str
    source_type: str
    num_chunks: int
    word_count: int
    is_indexed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    success: bool
    document_id: int
    title: str
    num_chunks: int
    word_count: int
    message: str


# ──────────────────────────────────────────────
# Health & Status
# ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    openai_configured: bool
    vector_store_docs: int
    db_connected: bool


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
