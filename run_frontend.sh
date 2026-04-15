#!/bin/bash
# ============================================================
# run_frontend.sh — Start the Streamlit frontend
# Usage: bash run_frontend.sh
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       StudyMate AI — Frontend        ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "🎓 Starting Streamlit on http://localhost:8501"
echo "   Make sure the backend is running first!"
echo ""

streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --theme.base dark \
    --theme.primaryColor "#818cf8" \
    --theme.backgroundColor "#0e0e13" \
    --theme.secondaryBackgroundColor "#13131a" \
    --theme.textColor "#e8e6df"
