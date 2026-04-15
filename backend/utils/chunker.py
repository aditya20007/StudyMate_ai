# ============================================================
# backend/utils/chunker.py — Text Chunking Utility
# ============================================================

import re
from typing import List
from dataclasses import dataclass, field
from loguru import logger

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


@dataclass
class TextChunk:
    """Represents a single chunk of text with its metadata."""
    text: str
    chunk_index: int
    source_doc_id: int = 0
    source_title: str = ""
    source_type: str = ""
    start_char: int = 0
    end_char: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.word_count = len(self.text.split())
        self.char_count = len(self.text)


class TextChunker:
    """
    Splits text into overlapping chunks for embedding.
    
    Strategy:
    1. Split on sentence boundaries (not arbitrary character positions)
    2. Group sentences into chunks of target size
    3. Add overlap between adjacent chunks for context continuity
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """
        Args:
            chunk_size: Target size in tokens (approx 4 chars/token).
            chunk_overlap: Number of tokens to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._token_encoder = None

    def _get_token_count(self, text: str) -> int:
        """Count tokens — uses tiktoken if available, else approx by words."""
        if TIKTOKEN_AVAILABLE:
            if self._token_encoder is None:
                self._token_encoder = tiktoken.get_encoding("cl100k_base")
            return len(self._token_encoder.encode(text))
        # Approximation: 1 token ≈ 0.75 words
        return int(len(text.split()) * 1.33)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Split on sentence-ending punctuation followed by whitespace
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out empty strings and very short fragments
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def chunk_text(
        self,
        text: str,
        doc_id: int = 0,
        title: str = "",
        source_type: str = "",
        extra_metadata: dict = None,
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks.

        Returns:
            List of TextChunk objects.
        """
        if not text.strip():
            raise ValueError("Cannot chunk empty text.")

        text = text.strip()
        sentences = self._split_into_sentences(text)

        if not sentences:
            # Fallback: split by newlines
            sentences = [p.strip() for p in text.split("\n") if p.strip()]

        chunks = []
        current_chunk_sentences = []
        current_token_count = 0
        char_pos = 0

        for sentence in sentences:
            sentence_tokens = self._get_token_count(sentence)

            # If single sentence exceeds chunk size, split it by words
            if sentence_tokens > self.chunk_size:
                # Flush current chunk first
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    chunks.append(
                        TextChunk(
                            text=chunk_text,
                            chunk_index=len(chunks),
                            source_doc_id=doc_id,
                            source_title=title,
                            source_type=source_type,
                            metadata=extra_metadata or {},
                        )
                    )
                    current_chunk_sentences = []
                    current_token_count = 0

                # Split the long sentence into word groups
                words = sentence.split()
                for i in range(0, len(words), self.chunk_size // 2):
                    word_group = " ".join(words[i : i + self.chunk_size // 2])
                    chunks.append(
                        TextChunk(
                            text=word_group,
                            chunk_index=len(chunks),
                            source_doc_id=doc_id,
                            source_title=title,
                            source_type=source_type,
                            metadata=extra_metadata or {},
                        )
                    )
                continue

            # If adding this sentence exceeds chunk size, save current chunk
            if current_token_count + sentence_tokens > self.chunk_size and current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        chunk_index=len(chunks),
                        source_doc_id=doc_id,
                        source_title=title,
                        source_type=source_type,
                        metadata=extra_metadata or {},
                    )
                )

                # Keep overlap: retain last N tokens worth of sentences
                overlap_sentences = []
                overlap_tokens = 0
                for s in reversed(current_chunk_sentences):
                    t = self._get_token_count(s)
                    if overlap_tokens + t <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += t
                    else:
                        break

                current_chunk_sentences = overlap_sentences
                current_token_count = overlap_tokens

            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens

        # Don't forget the last chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    chunk_index=len(chunks),
                    source_doc_id=doc_id,
                    source_title=title,
                    source_type=source_type,
                    metadata=extra_metadata or {},
                )
            )

        logger.info(
            f"Chunked '{title}' into {len(chunks)} chunks "
            f"(avg {sum(c.word_count for c in chunks)//max(len(chunks),1)} words each)"
        )
        return chunks
