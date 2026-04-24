# ============================================================
# run_backend.ps1 — Start the FastAPI backend (Windows)
# Usage: .\run_backend.ps1
# ============================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       StudyMate AI — Backend         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check for .env
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env — please set your OPENAI_API_KEY!" -ForegroundColor Green
    Write-Host ""
}

# Create required directories
$dirs = @("data\uploads", "audio_outputs", "vector_store_data", "data\logs")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Created: $dir" -ForegroundColor Gray
    }
}

Write-Host "🚀 Starting FastAPI backend on http://localhost:8000" -ForegroundColor Green
Write-Host "📚 Swagger docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
