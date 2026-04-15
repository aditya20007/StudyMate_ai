# ============================================================
# backend/main.py — FastAPI Application Entry Point (Render-Ready)
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
from backend.routes.upload import router as upload_router
from backend.routes.query import router as query_router


# ──────────────────────────────────────────────
# Create dirs BEFORE app object is built
# (StaticFiles mount fails if directory missing)
# ──────────────────────────────────────────────

Path("./data/uploads").mkdir(parents=True, exist_ok=True)
Path("./audio_outputs").mkdir(exist_ok=True)
Path("./vector_store_data").mkdir(exist_ok=True)
Path("./data/logs").mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StudyMate AI — Backend Starting")
    init_db()
    logger.info("StudyMate AI is ready!")
    yield
    logger.info("StudyMate AI shutting down...")


# ──────────────────────────────────────────────
# App
# ──────────────────────────────────────────────

app = FastAPI(
    title="StudyMate AI",
    description="AI-powered learning assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Static Files (audio)
# ──────────────────────────────────────────────

app.mount("/audio", StaticFiles(directory="./audio_outputs"), name="audio")


# ──────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────

app.include_router(upload_router)
app.include_router(query_router)


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/", tags=["Status"])
async def root():
    return {
        "app": "StudyMate AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Status"])
async def health_check():
    from rag.vector_store import get_vector_store   # ← remove "backend."
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

    vs = get_vector_store()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "groq_configured": settings.groq_api_key != "gsk_placeholder",
        "vector_store_docs": vs.total_vectors,
        "db_connected": db_ok,
    }


@app.get("/stats", tags=["Status"])
async def get_stats():
    from rag.vector_store import get_vector_store
    return get_vector_store().get_stats()


# ──────────────────────────────────────────────
# Error Handler
# ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ──────────────────────────────────────────────
# Entry point — reads PORT correctly on Render
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,   # Never reload in production
        log_level="info",
    )
