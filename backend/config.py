# ============================================================
# backend/config.py — Centralized Configuration (Render-Ready)
# ============================================================

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """
    Settings loaded from environment variables.
    On Render: set these in the dashboard Environment tab.
    Locally: put them in .env file.
    """

    # Groq (LLM — summarize, Q&A, quiz, study plan)
    groq_api_key: str = Field(default="gsk_placeholder", env="GROQ_API_KEY")

    # Google (FREE embeddings — text-embedding-004)
    # Get key at: https://aistudio.google.com/apikey
    google_api_key: str = Field(default="google_placeholder", env="GOOGLE_API_KEY")

    # App
    app_env: str = Field(default="production", env="APP_ENV")
    debug: bool = Field(default=False, env="DEBUG")
    app_secret_key: str = Field(default="change-me-in-prod", env="APP_SECRET_KEY")

    # Database
    database_url: str = Field(default="sqlite:///./data/studymate.db", env="DATABASE_URL")

    # Vector Store
    vector_store_path: str = Field(
        default="./vector_store_data/faiss_index", env="VECTOR_STORE_PATH"
    )

    # Audio
    audio_output_dir: str = Field(default="./audio_outputs", env="AUDIO_OUTPUT_DIR")

    # Chunking
    chunk_size: int = Field(default=800, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")

    # RAG
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")

    # Backend
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=10000, env="BACKEND_PORT")

    # Frontend
    frontend_backend_url: str = Field(
        default="http://localhost:8000", env="FRONTEND_BACKEND_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def ensure_directories(self):
        for d in ["./data", "./audio_outputs", "./vector_store_data", "./data/logs"]:
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()