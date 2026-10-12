# EduSense AI Windows Development Launcher
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting EduSense AI Platform on Windows" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$ROOT_DIR = $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"

# Check if .env exists
if (-not (Test-Path (Join-Path $ROOT_DIR ".env"))) {
    Write-Host "[+] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item (Join-Path $ROOT_DIR ".env.example") (Join-Path $ROOT_DIR ".env")
}

# Check virtualenv
$VENV_PYTHON = Join-Path $BACKEND_DIR "venv\Scripts\python.exe"
if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "[+] Creating virtual environment in backend/venv..." -ForegroundColor Yellow
    Set-Location $BACKEND_DIR
    python -m venv venv
    Set-Location $ROOT_DIR
}

Write-Host "[+] Upgrading database schema (Alembic)..." -ForegroundColor Green
Start-Process -FilePath $VENV_PYTHON -ArgumentList "-m alembic upgrade head" -WorkingDirectory $BACKEND_DIR -NoNewWindow -Wait

Write-Host "[+] Launching Backend Server (http://localhost:8000)..." -ForegroundColor Green
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BACKEND_DIR'; .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000" -PassThru

$LIVEKIT_EXE = Join-Path $ROOT_DIR "livekit-bin\livekit-server.exe"
if (Test-Path $LIVEKIT_EXE) {
    Write-Host "[+] Launching LiveKit WebRTC Server (http://localhost:7880)..." -ForegroundColor Green
    $livekitJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR'; .\livekit-bin\livekit-server.exe --dev --keys 'devkey: secret'" -PassThru
}

Write-Host "[+] Launching Frontend Server (http://localhost:5173)..." -ForegroundColor Green
$frontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FRONTEND_DIR'; npm run dev" -PassThru

Write-Host "`n[✓] EduSense AI is running!" -ForegroundColor Green
Write-Host "  - Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  - Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - LiveKit:   http://localhost:7880`n" -ForegroundColor Cyan

