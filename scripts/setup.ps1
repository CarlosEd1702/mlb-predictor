param(
    [string]$PythonPath = "python"
)

Write-Host "=== MLB Predictor Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Create virtual environment
Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Yellow
& $PythonPath -m venv .venv
if (-not $?) { Write-Error "Failed to create venv"; exit 1 }

# 2. Activate and install deps
Write-Host "[2/5] Installing backend dependencies..." -ForegroundColor Yellow
$pip = if ($env:OS -eq "Windows_NT") { ".\.venv\Scripts\pip" } else { ".\.venv/bin/pip" }
& $pip install -e "backend/[dev,ml]"
if (-not $?) { Write-Error "pip install failed"; exit 1 }

# 3. Create .env if not present
Write-Host "[3/5] Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "  Created backend\.env — edit ODDS_API_KEY"
}

# 4. Run initial migration
Write-Host "[4/5] Running database migration..." -ForegroundColor Yellow
$alembic = if ($env:OS -eq "Windows_NT") { ".\.venv\Scripts\alembic" } else { ".\.venv/bin/alembic" }
& $alembic upgrade head
if (-not $?) { Write-Warning "Migration failed — check PostgreSQL is running" }

# 5. Install Expo deps
Write-Host "[5/5] Installing Expo dependencies..." -ForegroundColor Yellow
if (Test-Path "app\package.json") {
    Push-Location app
    npm install
    Pop-Location
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "Run:  .\.venv\Scripts\activate  (or .venv/bin/activate on Linux)"
Write-Host "Then: uvicorn app.main:app --reload"
