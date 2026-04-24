# ============================================================
# backend/main.py — FastAPI Entry Point (Render-Optimised)
# ============================================================
#
# RAM Strategy for Render free tier (512MB):
#   Startup:        ~120MB  (fastapi + sqlalchemy + faiss)
#   After warmup:   ~180MB  (+ 17MB sentence-transformer model)
#   Safe headroom:  ~330MB  free
#
# The embedding model is NOT imported or loaded at startup.
# It loads lazily on the FIRST upload request only.
# ============================================================

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from loguru import logger

from backend.config import settings
from backend.database.session import init_db

# ── Create directories before anything else ──────────────────
Path("./data/uploads").mkdir(parents=True, exist_ok=True)
Path("./audio_outputs").mkdir(exist_ok=True)
Path("./vector_store_data").mkdir(exist_ok=True)
Path("./data/logs").mkdir(parents=True, exist_ok=True)


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StudyMate AI — Starting")
    init_db()
    logger.info("Database ready")
    # NOTE: embedding model is NOT loaded here
    # It loads lazily on first upload request (saves ~60MB RAM at startup)
    logger.info("StudyMate AI is ready!")
    yield
    logger.info("StudyMate AI — Shutting down")


# ── App ───────────────────────────────────────────────────────

app = FastAPI(
    title="StudyMate AI",
    description="AI-powered learning assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory="./audio_outputs"), name="audio")

# Import routers AFTER app creation (avoids circular import issues)
from backend.routes.upload import router as upload_router   # noqa: E402
from backend.routes.query  import router as query_router    # noqa: E402

app.include_router(upload_router)
app.include_router(query_router)


# ── Routes ────────────────────────────────────────────────────

@app.get("/", tags=["Status"])
async def root():
    return {"app": "StudyMate AI", "version": "1.0.0", "status": "running"}


@app.get("/health", tags=["Status"])
async def health_check():
    """
    Lightweight health check — does NOT load the embedding model.
    Render calls this every 30s to keep the service alive.
    """
    from backend.database.session import get_session_local
    from sqlalchemy import text

    db_ok = False
    try:
        db = get_session_local()()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        pass

    # Import vector store lazily too
    try:
        from rag.vector_store import get_vector_store
        vec_count = get_vector_store().total_vectors
    except Exception:
        vec_count = 0

    return {
        "status": "healthy",
        "version": "1.0.0",
        "groq_configured": settings.groq_api_key not in ("gsk_placeholder", ""),
        "vector_store_docs": vec_count,
        "db_connected": db_ok,
    }


@app.get("/stats", tags=["Status"])
async def get_stats():
    from rag.vector_store import get_vector_store
    return get_vector_store().get_stats()


# ── Error Handler ─────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ── Entry Point ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port,
                reload=False, log_level="info")