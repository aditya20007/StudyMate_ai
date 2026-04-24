# ============================================================
# backend/database/session.py — DB Engine & Session Factory
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Import settings lazily to avoid circular imports
def _get_database_url():
    from backend.config import settings
    return settings.database_url


Base = declarative_base()

# We create engine lazily so settings are loaded first
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = _get_database_url()
        connect_args = {}
        if "sqlite" in db_url:
            # SQLite needs check_same_thread=False for FastAPI async
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=False,  # Set True to see SQL logs
        )
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def init_db():
    """Create all tables defined in models."""
    # Import models so they register with Base metadata
    import backend.models.db_models  # noqa: F401
    Base.metadata.create_all(bind=get_engine())


def get_db():
    """
    FastAPI dependency — yields a DB session and ensures it's closed.
    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
