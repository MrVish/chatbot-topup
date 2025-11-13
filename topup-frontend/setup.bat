@echo off
REM Topup Frontend Setup Script
REM This script installs all required dependencies using pnpm

echo Setting up Topup Frontend...
echo.

REM Check if pnpm is installed
where pnpm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: pnpm is not installed.
    echo Please install pnpm first:
    echo   npm install -g pnpm
    echo   or visit: https://pnpm.io/installation
    exit /b 1
)

echo Installing dependencies with pnpm...
pnpm install

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Setup complete!
    echo.
    echo To start the development server, run:
    echo   pnpm dev
    echo.
    echo The application will be available at http://localhost:3000
) else (
    echo.
    echo Setup failed. Please check the error messages above.
    exit /b 1
)
