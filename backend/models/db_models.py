# ============================================================
# backend/models/db_models.py — SQLAlchemy ORM Models
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.session import Base


class User(Base):
    """
    Basic user model — extensible for auth in future.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("QueryHistory", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """
    Tracks every piece of content uploaded to the system.
    source_type: 'pdf' | 'youtube' | 'text'
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(300), nullable=False)
    source_type = Column(String(50), nullable=False)  # pdf | youtube | text
    source_url = Column(Text, nullable=True)           # YouTube URL or file path
    file_path = Column(Text, nullable=True)            # Local path for uploaded files
    num_chunks = Column(Integer, default=0)            # How many chunks were indexed
    word_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)        # Has it been embedded into FAISS?
    metadata_json = Column(JSON, nullable=True)        # Any extra metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="documents")
    queries = relationship("QueryHistory", back_populates="document")


class QueryHistory(Base):
    """
    Stores every Q&A interaction for analytics and history.
    """
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    query_type = Column(String(50), default="qa")   # qa | summarize | quiz
    sources_used = Column(JSON, nullable=True)       # List of source references
    confidence_score = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)      # Response time in ms
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="queries")
    document = relationship("Document", back_populates="queries")


class AudioFile(Base):
    """
    Tracks generated TTS audio files.
    """
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    text_hash = Column(String(64), index=True)          # MD5 hash to avoid re-generating
    file_path = Column(Text, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
