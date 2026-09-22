@echo off
title Ocean Atlas - ESP32 Flash (COM7)
color 0A
echo.
echo  ================================================
echo    Flashing ESP32 firmware to COM7...
echo  ================================================
echo.
echo  NOTE: If you see "Connecting........" stalling,
echo  hold the BOOT button on your ESP32 until you
echo  see "Uploading...", then release it.
echo.
cd /d "d:\DESKTOP\OCEAN AT\esp32\OCEAN ATLAS"
C:\Users\nithishraju\.platformio\penv\Scripts\pio.exe run -e esp32dev -t upload
if %errorlevel% neq 0 (
    echo.
    echo  *** UPLOAD FAILED ***
    echo  Check: Is ESP32 connected on COM7?
    echo  Try holding BOOT button during upload.
    pause
    exit
)
echo.
echo  ================================================
echo    Upload complete! Starting serial monitor...
echo    Press Ctrl+C to stop the monitor.
echo  ================================================
echo.
C:\Users\nithishraju\.platformio\penv\Scripts\pio.exe device monitor --baud 115200 --port COM7
pause
