# ============================================================
# backend/services/tts_service.py — Text-to-Speech via gTTS
# ============================================================

import hashlib
import os
from pathlib import Path
from loguru import logger
from gtts import gTTS
from backend.config import settings


class TTSService:
    """
    Converts text to speech using Google Text-to-Speech (gTTS).
    
    Features:
    - Caches audio files by text hash to avoid re-generation
    - Supports multiple languages
    - Returns file path for streaming
    """

    def __init__(self):
        self.output_dir = Path(settings.audio_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def text_to_speech(
        self, text: str, language: str = "en", document_id: int = None
    ) -> dict:
        """
        Convert text to an MP3 audio file.

        Args:
            text: The text to convert.
            language: Language code (e.g., 'en', 'hi', 'fr').
            document_id: Optional document ID for naming.

        Returns:
            dict with 'file_path', 'text_hash', 'cached'
        """
        # Clean text for TTS
        clean_text = self._prepare_text(text)

        if not clean_text:
            raise ValueError("Text is empty after cleaning. Cannot generate audio.")

        # Generate a hash for caching
        text_hash = hashlib.md5(f"{clean_text}{language}".encode()).hexdigest()
        file_name = f"audio_{text_hash}.mp3"
        file_path = self.output_dir / file_name

        # Return cached version if it exists
        if file_path.exists():
            logger.info(f"Returning cached audio: {file_name}")
            return {
                "file_path": str(file_path),
                "text_hash": text_hash,
                "cached": True,
            }

        # Generate new audio
        logger.info(f"Generating TTS audio ({language}) — {len(clean_text)} chars")
        try:
            tts = gTTS(text=clean_text, lang=language, slow=False)
            tts.save(str(file_path))
            logger.info(f"Audio saved to: {file_path}")
        except Exception as e:
            raise RuntimeError(f"gTTS failed: {e}. Check internet connection.")

        return {
            "file_path": str(file_path),
            "text_hash": text_hash,
            "cached": False,
        }

    @staticmethod
    def _prepare_text(text: str) -> str:
        """
        Prepare text for TTS:
        - Strip markdown formatting
        - Limit length (gTTS has limits)
        - Clean special characters
        """
        import re

        # Remove markdown
        text = re.sub(r"[*_`#>]", "", text)
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)  # Remove links

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)

        # Limit to 4500 chars to avoid gTTS issues
        if len(text) > 4500:
            text = text[:4500] + "... (truncated for audio)"

        return text.strip()

    def list_audio_files(self) -> list:
        """List all generated audio files."""
        return [
            {"file_name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
            for f in self.output_dir.glob("*.mp3")
        ]

    def cleanup_old_files(self, max_files: int = 50):
        """Remove oldest audio files if limit exceeded."""
        files = sorted(self.output_dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime)
        while len(files) > max_files:
            files[0].unlink()
            logger.info(f"Deleted old audio: {files[0].name}")
            files.pop(0)
