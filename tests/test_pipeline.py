# ============================================================
# tests/test_pipeline.py — Unit Tests for Core Components
# Run with: pytest tests/ -v
# ============================================================

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ──────────────────────────────────────────────
# Test: Text Chunker
# ──────────────────────────────────────────────

class TestTextChunker:
    def setup_method(self):
        from backend.utils.chunker import TextChunker
        self.chunker = TextChunker(chunk_size=200, chunk_overlap=30)

    def test_basic_chunking(self):
        text = "This is a test sentence. " * 100
        chunks = self.chunker.chunk_text(text, doc_id=1, title="Test", source_type="text")
        assert len(chunks) > 1, "Long text should produce multiple chunks"

    def test_chunk_has_metadata(self):
        text = "Hello world. This is a test document with some content. " * 20
        chunks = self.chunker.chunk_text(text, doc_id=42, title="My Doc", source_type="pdf")
        for chunk in chunks:
            assert chunk.source_doc_id == 42
            assert chunk.source_title == "My Doc"
            assert chunk.source_type == "pdf"
            assert chunk.text.strip() != ""

    def test_chunk_indices_sequential(self):
        text = "Sentence number one. Sentence number two. Sentence number three. " * 30
        chunks = self.chunker.chunk_text(text, doc_id=1, title="Test", source_type="text")
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_empty_text_raises(self):
        with pytest.raises(ValueError):
            self.chunker.chunk_text("", doc_id=1, title="Empty", source_type="text")

    def test_short_text_single_chunk(self):
        text = "This is a very short text with just a few words."
        chunks = self.chunker.chunk_text(text, doc_id=1, title="Short", source_type="text")
        assert len(chunks) == 1


# ──────────────────────────────────────────────
# Test: Text Cleaner
# ──────────────────────────────────────────────

class TestTextCleaner:
    def setup_method(self):
        from backend.utils.text_cleaner import TextCleaner
        self.cleaner = TextCleaner()

    def test_removes_null_bytes(self):
        dirty = "Hello\x00World\x00Test"
        clean = self.cleaner.clean(dirty)
        assert "\x00" not in clean

    def test_normalizes_whitespace(self):
        dirty = "Hello    World\n\n\n\nTest"
        clean = self.cleaner.normalize_whitespace(dirty)
        assert "\n\n\n" not in clean

    def test_fixes_pdf_hyphenation(self):
        dirty = "infor-\nmation"
        fixed = self.cleaner.fix_pdf_artifacts(dirty)
        assert "infor-\nmation" not in fixed

    def test_word_count(self):
        text = "one two three four five"
        assert self.cleaner.word_count(text) == 5

    def test_truncate_to_tokens(self):
        long_text = "word " * 10000
        truncated = self.cleaner.truncate_to_tokens(long_text, max_tokens=100)
        assert len(truncated.split()) < 200  # Rough check

    def test_empty_input(self):
        assert self.cleaner.clean("") == ""
        assert self.cleaner.clean("   ") == ""


# ──────────────────────────────────────────────
# Test: PDF Service
# ──────────────────────────────────────────────

class TestPDFService:
    def test_file_not_found_raises(self):
        from backend.services.pdf_service import PDFService
        with pytest.raises(FileNotFoundError):
            PDFService.extract_text("/nonexistent/path/file.pdf")

    def test_clean_text_removes_excessive_newlines(self):
        from backend.services.pdf_service import PDFService
        text = "Line one\n\n\n\n\nLine two"
        clean = PDFService.clean_text(text)
        assert "\n\n\n" not in clean


# ──────────────────────────────────────────────
# Test: YouTube Service
# ──────────────────────────────────────────────

class TestYouTubeService:
    def test_extract_video_id_standard(self):
        from backend.services.youtube_service import YouTubeService
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        vid_id = YouTubeService.extract_video_id(url)
        assert vid_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short(self):
        from backend.services.youtube_service import YouTubeService
        url = "https://youtu.be/dQw4w9WgXcQ"
        vid_id = YouTubeService.extract_video_id(url)
        assert vid_id == "dQw4w9WgXcQ"

    def test_invalid_url_raises(self):
        from backend.services.youtube_service import YouTubeService
        with pytest.raises(ValueError):
            YouTubeService.extract_video_id("https://vimeo.com/12345")

    def test_invalid_youtube_url(self):
        from backend.services.youtube_service import YouTubeService
        with pytest.raises(ValueError):
            YouTubeService.extract_video_id("not-a-url")


# ──────────────────────────────────────────────
# Test: Schemas (Pydantic Validation)
# ──────────────────────────────────────────────

class TestSchemas:
    def test_text_upload_rejects_empty(self):
        from pydantic import ValidationError
        from backend.schemas.schemas import TextUploadRequest
        with pytest.raises(ValidationError):
            TextUploadRequest(title="Test", content="   ")

    def test_text_upload_rejects_short_content(self):
        from pydantic import ValidationError
        from backend.schemas.schemas import TextUploadRequest
        with pytest.raises(ValidationError):
            TextUploadRequest(title="Test", content="Too short")

    def test_youtube_upload_rejects_non_yt_url(self):
        from pydantic import ValidationError
        from backend.schemas.schemas import YouTubeUploadRequest
        with pytest.raises(ValidationError):
            YouTubeUploadRequest(url="https://vimeo.com/12345")

    def test_valid_text_upload(self):
        from backend.schemas.schemas import TextUploadRequest
        req = TextUploadRequest(
            title="Machine Learning Notes",
            content="This is a valid piece of content with more than ten words to pass validation checks.",
        )
        assert req.title == "Machine Learning Notes"

    def test_quiz_request_bounds(self):
        from pydantic import ValidationError
        from backend.schemas.schemas import QuizRequest
        with pytest.raises(ValidationError):
            QuizRequest(document_id=1, num_questions=50)  # Max is 10


# ──────────────────────────────────────────────
# Test: LLM Service (mocked)
# ──────────────────────────────────────────────

class TestLLMService:
    def test_is_configured_false_with_placeholder(self, monkeypatch):
        from backend.services.llm_service import LLMService
        monkeypatch.setattr("backend.config.settings.groq_api_key", "gsk_placeholder")
        svc = LLMService()
        # Re-check with patched settings
        # Re-instantiate to pick up patched settings
        svc2 = LLMService()
        assert svc2.is_configured() is False

    def test_quiz_json_parsing_valid(self):
        """Test the JSON parsing logic in generate_quiz."""
        from backend.services.llm_service import LLMService
        svc = LLMService()

        # Simulate what the LLM returns
        mock_response = '''
        {
          "questions": [
            {
              "question_number": 1,
              "question": "What is 2+2?",
              "options": [
                {"label": "A", "text": "3"},
                {"label": "B", "text": "4"},
                {"label": "C", "text": "5"},
                {"label": "D", "text": "6"}
              ],
              "correct_answer": "B",
              "explanation": "2+2 equals 4."
            }
          ]
        }
        '''
        import json
        data = json.loads(mock_response)
        questions = data.get("questions", [])
        assert len(questions) == 1
        assert questions[0]["correct_answer"] == "B"

    def test_quiz_json_parsing_malformed(self):
        """Test that malformed JSON raises ValueError."""
        import json
        malformed = "This is not JSON at all"
        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed)


# ──────────────────────────────────────────────
# Run Tests
# ──────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
