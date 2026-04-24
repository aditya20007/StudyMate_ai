#!/bin/bash
# ============================================================
# run_backend.sh — Start the FastAPI backend
# Usage: bash run_backend.sh
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       StudyMate AI — Backend         ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check for .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env — please set your OPENAI_API_KEY!"
    echo ""
fi

# Create required directories
mkdir -p data/uploads audio_outputs vector_store_data data/logs

echo "🚀 Starting FastAPI backend on http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""

python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
