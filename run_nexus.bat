@echo off
TITLE NEXUS — Autonomous Web Intelligence Agent
echo ==============================================================================
echo        NEXUS — Autonomous Web Intelligence Agent (v2.0.0)
echo ==============================================================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found in .venv. Using system Python...
)

echo Starting NEXUS FastAPI & Web Application Server on http://127.0.0.1:8000 ...
echo [API Docs available at: http://127.0.0.1:8000/docs]
echo.

python -m uvicorn server.app:app --host 127.0.0.1 --port 8000
pause
