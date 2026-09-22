@echo off
title Ocean Atlas – Start All Services
color 0B

echo.
echo  ============================================
echo    OCEAN ATLAS – Starting All Services
echo  ============================================
echo.

REM ── 1. FastAPI Backend (port 8000) ──────────────────────────────────────
echo  [1/3] Starting FastAPI Backend on port 8000...
start "Ocean Atlas – Backend" cmd /k "cd /d d:\DESKTOP\OCEAN AT && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

REM ── 2. React Frontend (port 5173) ───────────────────────────────────────
echo  [2/3] Starting React Frontend on port 5173...
start "Ocean Atlas – Frontend" cmd /k "cd /d d:\DESKTOP\OCEAN AT && npm run dev"

timeout /t 4 /nobreak >nul

REM ── 3. PlatformIO Build + Flash + Monitor (COM7) ────────────────────────
echo  [3/3] Building and flashing ESP32 firmware to COM7...
echo.
echo  NOTE: If upload fails with "Failed to connect", 
echo        hold the BOOT button on the ESP32 while it
echo        says "Connecting...", then release it.
echo.
start "Ocean Atlas – ESP32 Flash" cmd /k "cd /d d:\DESKTOP\OCEAN AT\esp32\OCEAN ATLAS && C:\Users\nithishraju\.platformio\penv\Scripts\pio.exe run -e esp32dev -t upload && echo. && echo Upload complete! Starting serial monitor... && C:\Users\nithishraju\.platformio\penv\Scripts\pio.exe device monitor --baud 115200 --port COM7"

echo.
echo  ============================================
echo    All services started in separate windows!
echo.
echo    Backend  : http://localhost:8000
echo    Frontend : http://localhost:5173/dashboard
echo    ESP32    : COM7 (Silicon Labs CP210x)
echo  ============================================
echo.
echo  Opening dashboard in browser...
timeout /t 5 /nobreak >nul
start http://localhost:5173/dashboard

echo.
echo  You can close this window.
pause
