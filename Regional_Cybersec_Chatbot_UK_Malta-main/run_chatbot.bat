@echo off
echo Starting Backend Server...
cd UK\backend
start "Backend Server" python main.py
cd ..\..
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul
echo Opening Frontend...
start UK\index.html
echo Application Started!
