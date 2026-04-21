@echo off
REM ─────────────────────────────────────────────────────────────
REM  CDR Analytics Dashboard — Auto-Restart Launcher
REM  Place this file in C:\CDR_Dashboard\
REM  Automatically restarts Streamlit if it crashes or stops.
REM ─────────────────────────────────────────────────────────────

:START
echo [%DATE% %TIME%] Starting CDR Dashboard... >> C:\CDR_Dashboard\logs\startup.log

cd /d C:\CDR_Dashboard

python -m streamlit run app.py ^
    --server.port 8501 ^
    --server.headless true ^
    --server.enableCORS false ^
    --server.address 0.0.0.0

REM If Streamlit exits for any reason, wait 5 seconds and restart
echo [%DATE% %TIME%] Dashboard stopped unexpectedly. Restarting in 5 seconds... >> C:\CDR_Dashboard\logs\startup.log
timeout /t 5 /nobreak >nul
goto START
