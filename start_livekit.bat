@echo off
echo ==================================================
echo  Starting LiveKit WebRTC Server for EduSense AI
echo ==================================================
echo.

cd /d %~dp0

if exist "livekit-bin\livekit-server.exe" (
    echo [+] Starting native LiveKit server on port 7880...
    livekit-bin\livekit-server.exe --dev --keys "devkey: secret"
    goto end
)

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Native LiveKit binary not found and Docker not found in PATH.
    echo     Please check livekit-bin\livekit-server.exe or start Docker Desktop.
    echo.
    pause
    exit /b 1
)

echo [+] Launching LiveKit Server container via Docker on port 7880...
docker run --rm -p 7880:7880 -p 7881:7881 -p 7882:7882/udp livekit/livekit-server --dev --keys "devkey: secret"

:end
pause

