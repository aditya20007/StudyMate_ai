# ============================================================
# backend/utils/text_cleaner.py — Text Preprocessing Utilities
# ============================================================

import re
import unicodedata
from typing import Optional


class TextCleaner:
    """
    Utility class for cleaning and normalizing text before indexing.
    Applied to all text regardless of source (PDF, YouTube, raw text).
    """

    @staticmethod
    def clean(text: str, aggressive: bool = False) -> str:
        """
        Full cleaning pipeline.

        Args:
            text: Raw input text.
            aggressive: If True, apply stricter normalization (good for PDFs).

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        # Step 1: Normalize unicode (handles accented chars, special quotes, etc.)
        text = unicodedata.normalize("NFKD", text)

        # Step 2: Remove null bytes and control characters
        text = TextCleaner.remove_control_chars(text)

        # Step 3: Fix common PDF extraction artifacts
        text = TextCleaner.fix_pdf_artifacts(text)

        # Step 4: Normalize whitespace
        text = TextCleaner.normalize_whitespace(text)

        # Step 5: Optional aggressive cleaning
        if aggressive:
            text = TextCleaner.remove_boilerplate(text)

        return text.strip()

    @staticmethod
    def remove_control_chars(text: str) -> str:
        """Remove ASCII control characters except newlines and tabs."""
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    @staticmethod
    def fix_pdf_artifacts(text: str) -> str:
        """Fix common issues from PDF text extraction."""
        # Remove hyphenation at line breaks (word wrap artifacts)
        text = re.sub(r"-\n(\w)", r"\1", text)

        # Fix missing spaces after periods (common in PDFs)
        text = re.sub(r"\.([A-Z])", r". \1", text)

        # Collapse multiple spaces into one (but not newlines)
        text = re.sub(r"[ \t]{2,}", " ", text)

        # Remove page number artifacts like "— 12 —" or "Page 12"
        text = re.sub(r"(?i)(page\s+\d+|—\s*\d+\s*—|\[\s*\d+\s*\])", "", text)

        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize all forms of whitespace."""
        # Replace Windows line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse more than 2 consecutive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip trailing whitespace from each line
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines)

    @staticmethod
    def remove_boilerplate(text: str) -> str:
        """
        Remove common boilerplate patterns.
        Useful for academic papers and web-scraped content.
        """
        # Remove URLs
        text = re.sub(r"https?://\S+", "[URL]", text)

        # Remove email addresses
        text = re.sub(r"\b[\w.+-]+@[\w-]+\.\w+\b", "[EMAIL]", text)

        # Remove long sequences of special characters (table borders, etc.)
        text = re.sub(r"[=\-_]{5,}", "", text)

        return text

    @staticmethod
    def truncate_to_tokens(text: str, max_tokens: int = 4000) -> str:
        """
        Truncate text to approximately max_tokens tokens.
        Uses word count as a proxy (avg ~1.3 words/token).
        """
        max_words = int(max_tokens / 1.33)
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words])
        return truncated + "\n\n[... content truncated for processing ...]"

    @staticmethod
    def extract_title_from_text(text: str, max_length: int = 80) -> Optional[str]:
        """
        Try to extract a title from the first non-empty line of text.
        Used as fallback when no explicit title is given.
        """
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return None

        first_line = lines[0]

        # If first line is reasonably short, use it as title
        if 5 <= len(first_line) <= max_length:
            # Remove markdown heading markers
            first_line = re.sub(r"^#+\s*", "", first_line)
            return first_line[:max_length]

        return None

    @staticmethod
    def word_count(text: str) -> int:
        """Count words in text."""
        return len(text.split())

    @staticmethod
    def sentence_count(text: str) -> int:
        """Estimate number of sentences."""
        return len(re.findall(r"[.!?]+", text))
