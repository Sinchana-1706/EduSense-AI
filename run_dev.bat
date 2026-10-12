@echo off
echo ==================================================
echo  Starting EduSense AI Platform on Windows
echo ==================================================

cd /d %~dp0

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Starting Backend Server on http://localhost:8000 ...
start "EduSense AI Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

if exist "livekit-bin\livekit-server.exe" (
    echo Starting LiveKit Server on http://localhost:7880 ...
    start "EduSense AI LiveKit" cmd /k "cd /d %~dp0 && livekit-bin\livekit-server.exe --dev --keys ""devkey: secret"""
)

echo Starting Frontend Server on http://localhost:5173 ...
start "EduSense AI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo [!] EduSense AI services launched in separate windows.
echo     Frontend: http://localhost:5173
echo     Backend:  http://localhost:8000/docs
echo     LiveKit:  http://localhost:7880
echo.
pause

