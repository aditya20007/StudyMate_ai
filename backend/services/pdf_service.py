# ============================================================
# backend/services/pdf_service.py — PDF Text Extraction
# ============================================================

import pdfplumber
import fitz  # PyMuPDF — used as fallback
from pathlib import Path
from loguru import logger
from typing import Tuple


class PDFService:
    """
    Extracts text from PDF files using pdfplumber (primary)
    with PyMuPDF as a fallback for scanned/complex PDFs.
    """

    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, dict]:
        """
        Extract all text from a PDF file.

        Returns:
            (full_text, metadata_dict)
        Raises:
            ValueError: If the PDF is empty or unreadable.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info(f"Extracting text from PDF: {path.name}")

        # --- Try pdfplumber first ---
        text, metadata = PDFService._extract_with_pdfplumber(file_path)

        # --- Fallback to PyMuPDF if pdfplumber yields little text ---
        if len(text.strip()) < 100:
            logger.warning("pdfplumber got little text, trying PyMuPDF fallback...")
            text, metadata = PDFService._extract_with_pymupdf(file_path)

        if not text.strip():
            raise ValueError(
                "PDF appears to be empty or image-only (scanned). "
                "Please use a text-based PDF."
            )

        word_count = len(text.split())
        metadata["word_count"] = word_count
        logger.info(f"Extracted {word_count} words from {path.name}")

        return text, metadata

    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> Tuple[str, dict]:
        """Extract using pdfplumber — better for tables and formatted docs."""
        pages_text = []
        metadata = {}

        with pdfplumber.open(file_path) as pdf:
            metadata["num_pages"] = len(pdf.pages)
            metadata["pdf_metadata"] = pdf.metadata or {}

            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(f"[Page {i+1}]\n{page_text}")

        full_text = "\n\n".join(pages_text)
        return full_text, metadata

    @staticmethod
    def _extract_with_pymupdf(file_path: str) -> Tuple[str, dict]:
        """Fallback extraction using PyMuPDF (fitz)."""
        pages_text = []
        metadata = {}

        doc = fitz.open(file_path)
        metadata["num_pages"] = len(doc)
        metadata["pdf_metadata"] = doc.metadata or {}

        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages_text.append(f"[Page {i+1}]\n{text}")

        doc.close()
        full_text = "\n\n".join(pages_text)
        return full_text, metadata

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted PDF text:
        - Remove excessive whitespace
        - Remove null bytes
        - Normalize line breaks
        """
        import re

        # Remove null bytes and control characters
        text = text.replace("\x00", "").replace("\r", "\n")

        # Collapse multiple blank lines to max 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove lines that are just whitespace
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()
