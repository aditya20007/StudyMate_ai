# ============================================================
# backend/services/youtube_service.py — YouTube Transcript Fetcher
# ============================================================

import re
import os
import tempfile
from typing import Tuple, Optional
from loguru import logger

try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    logger.warning("youtube-transcript-api not installed. YouTube support limited.")


class YouTubeService:
    """
    Fetches transcripts from YouTube videos.
    Priority:
      1. YouTube Transcript API (fast, free)
      2. yt-dlp audio download + Whisper transcription (fallback)
    """

    @staticmethod
    def extract_video_id(url: str) -> str:
        """
        Parse YouTube video ID from any common URL format.
        Handles:
          - https://www.youtube.com/watch?v=VIDEO_ID
          - https://youtu.be/VIDEO_ID
          - https://youtube.com/shorts/VIDEO_ID
        """
        patterns = [
            r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Could not extract video ID from URL: {url}")

    @staticmethod
    def get_transcript(url: str) -> Tuple[str, dict]:
        """
        Get transcript for a YouTube video.

        Returns:
            (transcript_text, metadata)
        Raises:
            ValueError: If transcript cannot be retrieved.
        """
        video_id = YouTubeService.extract_video_id(url)
        logger.info(f"Fetching transcript for video ID: {video_id}")

        # --- Method 1: YouTube Transcript API ---
        if TRANSCRIPT_API_AVAILABLE:
            try:
                return YouTubeService._fetch_via_transcript_api(video_id, url)
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                logger.warning(f"No captions available: {e}. Trying Whisper fallback...")
            except Exception as e:
                logger.warning(f"Transcript API failed: {e}. Trying Whisper fallback...")

        # --- Method 2: Whisper Fallback ---
        try:
            return YouTubeService._fetch_via_whisper(url, video_id)
        except Exception as e:
            raise ValueError(
                f"Could not retrieve transcript. "
                f"Video may have no captions and Whisper fallback failed: {e}"
            )

    @staticmethod
    def _fetch_via_transcript_api(video_id: str, url: str) -> Tuple[str, dict]:
        """Use YouTubeTranscriptApi to get captions."""
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try English first, then auto-generated, then any available
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                # Get first available transcript
                for t in transcript_list:
                    transcript = t
                    break

        if transcript is None:
            raise NoTranscriptFound(video_id, ["en"], transcript_list)

        entries = transcript.fetch()

        # Combine transcript with timestamps
        full_text_parts = []
        timestamped_parts = []

        for entry in entries:
            text = entry.get("text", "").strip()
            start = entry.get("start", 0)
            if text:
                full_text_parts.append(text)
                mins = int(start // 60)
                secs = int(start % 60)
                timestamped_parts.append(f"[{mins:02d}:{secs:02d}] {text}")

        full_text = " ".join(full_text_parts)
        timestamped_text = "\n".join(timestamped_parts)

        metadata = {
            "video_id": video_id,
            "url": url,
            "transcript_language": transcript.language_code,
            "is_auto_generated": transcript.is_generated,
            "num_segments": len(entries),
            "timestamped_text": timestamped_text,
        }

        logger.info(f"Fetched transcript: {len(full_text.split())} words")
        return full_text, metadata

    @staticmethod
    def _fetch_via_whisper(url: str, video_id: str) -> Tuple[str, dict]:
        """
        Download audio with yt-dlp and transcribe with Whisper.
        This is the fallback for videos without captions.
        """
        import whisper
        import yt_dlp

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"{video_id}.mp3")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, f"{video_id}.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }],
                "quiet": True,
                "no_warnings": True,
            }

            logger.info("Downloading audio with yt-dlp...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get("title", "Unknown Video")

            logger.info("Transcribing audio with Whisper (this may take a minute)...")
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            text = result.get("text", "")

            metadata = {
                "video_id": video_id,
                "url": url,
                "transcript_method": "whisper",
                "video_title": video_title,
            }

            return text, metadata

    @staticmethod
    def get_video_title(url: str) -> Optional[str]:
        """Attempt to get the video title via yt-dlp."""
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("title")
        except Exception:
            return None
