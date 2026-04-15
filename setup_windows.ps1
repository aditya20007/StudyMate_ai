# ============================================================
# setup_windows.ps1 — One-click Windows setup for StudyMate AI
# Usage: .\setup_windows.ps1
# ============================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     StudyMate AI — Windows Setup           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check Python version ────────────────────────────
Write-Host "📋 Step 1: Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found! Please install Python 3.9+ from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green

# ── Step 2: Create virtual environment ──────────────────────
Write-Host ""
Write-Host "📋 Step 2: Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists." -ForegroundColor Green
}

# ── Step 3: Activate venv ───────────────────────────────────
Write-Host ""
Write-Host "📋 Step 3: Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✅ Activated." -ForegroundColor Green

# ── Step 4: Upgrade pip ─────────────────────────────────────
Write-Host ""
Write-Host "📋 Step 4: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✅ pip upgraded." -ForegroundColor Green

# ── Step 5: Install packages (in correct order) ─────────────
Write-Host ""
Write-Host "📋 Step 5: Installing packages (this takes 3-10 minutes)..." -ForegroundColor Yellow
Write-Host "   Installing core packages..." -ForegroundColor Gray

# Install in groups to avoid resolver conflicts
$corePackages = @(
    "fastapi", "uvicorn[standard]", "python-multipart",
    "sqlalchemy", "aiosqlite",
    "pydantic", "pydantic-settings",
    "python-dotenv", "loguru", "tenacity",
    "requests", "httpx", "aiofiles", "rich", "tqdm"
)

$aiPackages = @(
    "openai", "tiktoken"
)

$mlPackages = @(
    "numpy", "sentence-transformers"
)

$appPackages = @(
    "streamlit", "streamlit-option-menu",
    "pdfplumber", "PyMuPDF",
    "youtube-transcript-api", "yt-dlp",
    "gTTS", "faiss-cpu"
)

foreach ($pkg in $corePackages) {
    Write-Host "   Installing $pkg..." -ForegroundColor Gray
    python -m pip install $pkg --quiet
}

foreach ($pkg in $aiPackages) {
    Write-Host "   Installing $pkg..." -ForegroundColor Gray
    python -m pip install $pkg --quiet
}

Write-Host "   Installing ML packages (numpy, sentence-transformers)..." -ForegroundColor Gray
foreach ($pkg in $mlPackages) {
    python -m pip install $pkg --quiet
}

Write-Host "   Installing app packages (streamlit, faiss, pdfplumber, etc.)..." -ForegroundColor Gray
foreach ($pkg in $appPackages) {
    Write-Host "   Installing $pkg..." -ForegroundColor Gray
    python -m pip install $pkg --quiet
}

Write-Host "✅ All packages installed." -ForegroundColor Green

# ── Step 6: Create .env ─────────────────────────────────────
Write-Host ""
Write-Host "📋 Step 6: Setting up .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env from .env.example" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Open .env and add your OPENAI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env already exists." -ForegroundColor Green
}

# ── Step 7: Create directories ──────────────────────────────
Write-Host ""
Write-Host "📋 Step 7: Creating required directories..." -ForegroundColor Yellow
$dirs = @("data\uploads", "audio_outputs", "vector_store_data", "data\logs")
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Write-Host "✅ Directories created." -ForegroundColor Green

# ── Step 8: Verify installation ─────────────────────────────
Write-Host ""
Write-Host "📋 Step 8: Verifying installation..." -ForegroundColor Yellow
$checks = @(
    @{name="fastapi"; cmd="python -c 'import fastapi; print(fastapi.__version__)'"},
    @{name="streamlit"; cmd="python -c 'import streamlit; print(streamlit.__version__)'"},
    @{name="uvicorn"; cmd="python -c 'import uvicorn; print(uvicorn.__version__)'"},
    @{name="faiss"; cmd="python -c 'import faiss; print(\"ok\")'"},
    @{name="sentence-transformers"; cmd="python -c 'from sentence_transformers import SentenceTransformer; print(\"ok\")'"},
    @{name="openai"; cmd="python -c 'import openai; print(openai.__version__)'"},
    @{name="pdfplumber"; cmd="python -c 'import pdfplumber; print(\"ok\")'"}
)

$allOk = $true
foreach ($check in $checks) {
    $result = Invoke-Expression $check.cmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $($check.name): $result" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $($check.name): FAILED — $result" -ForegroundColor Red
        $allOk = $false
    }
}

# ── Done ────────────────────────────────────────────────────
Write-Host ""
if ($allOk) {
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║           ✅ Setup Complete!               ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Edit .env and add your OPENAI_API_KEY" -ForegroundColor White
    Write-Host "  2. Open Terminal 1: .\run_backend.ps1" -ForegroundColor White
    Write-Host "  3. Open Terminal 2: .\run_frontend.ps1" -ForegroundColor White
    Write-Host "  4. Visit: http://localhost:8501" -ForegroundColor White
} else {
    Write-Host "⚠️  Some packages failed. Try running manually:" -ForegroundColor Yellow
    Write-Host "   pip install -r requirements.txt" -ForegroundColor White
}
Write-Host ""
