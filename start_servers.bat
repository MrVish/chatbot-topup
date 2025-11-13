@echo off
echo ================================================================================
echo TOPUP CXO ASSISTANT - Starting Servers
echo ================================================================================
echo.

REM Check if backend virtual environment exists
if not exist "topup-backend\venv" (
    echo ERROR: Backend virtual environment not found!
    echo Please run: cd topup-backend ^&^& setup.bat
    pause
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "topup-frontend\node_modules" (
    echo ERROR: Frontend dependencies not installed!
    echo Please run: cd topup-frontend ^&^& pnpm install
    pause
    exit /b 1
)

REM Check if database exists
if not exist "topup-backend\data\topup.db" (
    echo WARNING: Database not found!
    echo Generating sample data...
    cd topup-backend
    call venv\Scripts\activate.bat
    python scripts\generate_sample_data.py
    call deactivate
    cd ..
    echo Sample data generated.
    echo.
)

echo Starting Backend Server (Port 8000)...
echo.
start "Topup Backend" cmd /k "cd topup-backend && venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend Server (Port 3000)...
echo.
start "Topup Frontend" cmd /k "cd topup-frontend && pnpm dev"

echo.
echo ================================================================================
echo Servers Starting...
echo ================================================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo Health:   http://localhost:8000/health
echo.
echo Press any key to open the application in your browser...
pause >nul

REM Open browser
start http://localhost:3000

echo.
echo ================================================================================
echo Servers are running!
echo ================================================================================
echo.
echo To stop servers, close the terminal windows or press Ctrl+C in each window.
echo.
pause
