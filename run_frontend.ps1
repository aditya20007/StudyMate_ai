# ============================================================
# run_frontend.ps1 — Start the Streamlit frontend (Windows)
# Usage: .\run_frontend.ps1
# ============================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║       StudyMate AI — Frontend        ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Host "🎓 Starting Streamlit on http://localhost:8501" -ForegroundColor Green
Write-Host "   Make sure the backend is running first!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

python -m streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
