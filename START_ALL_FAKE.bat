@echo off
title Ocean Atlas - Fake Data
echo Starting Backend...
start "Ocean Atlas - Backend" cmd /k "cd /d ""%~dp0backend"" && uvicorn main:app --host 0.0.0.0 --port 8000"

ping 127.0.0.1 -n 4 > nul

echo Starting Fake Data Simulator...
start "Ocean Atlas - Simulator" cmd /k "cd /d ""%~dp0backend"" && python simulate_device.py"

echo Starting Frontend...
start "Ocean Atlas - Frontend" cmd /k "cd /d ""%~dp0"" && npm run dev"

echo Services started!

