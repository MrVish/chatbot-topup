@echo off

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start FastAPI server
uvicorn app.main:app --reload --port 8000
