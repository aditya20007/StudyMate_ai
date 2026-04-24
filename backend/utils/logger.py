# ============================================================
# backend/utils/logger.py — Loguru Logger Configuration
# ============================================================

import sys
from loguru import logger
from pathlib import Path


def setup_logger(log_level: str = "INFO", log_to_file: bool = True):
    """
    Configure loguru logger for the application.

    Features:
    - Colored console output
    - Rotating file logs (daily rotation, 7 days retention)
    - Structured format with timestamps
    """
    # Remove default handler
    logger.remove()

    # Console handler — colored, human-readable
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File handler — JSON-structured for log aggregation tools
    if log_to_file:
        log_dir = Path("./data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_dir / "studymate_{time:YYYY-MM-DD}.log"),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} — {message}",
            rotation="00:00",      # New file at midnight
            retention="7 days",    # Keep 7 days of logs
            compression="zip",     # Compress old logs
            enqueue=True,          # Thread-safe
        )

    return logger


# Initialize on import
setup_logger()
