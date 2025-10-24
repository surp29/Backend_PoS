@echo off
REM PhanMemKeToan Backend Startup Script
REM Professional FastAPI Backend Server

echo.
echo ========================================
echo   PhanMemKeToan Backend Server
echo   Professional FastAPI Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found
    echo [INFO] Copying from env.example...
    copy env.example .env
    if errorlevel 1 (
        echo [ERROR] Failed to copy env.example
        pause
        exit /b 1
    )
    echo [INFO] Please edit .env file with your configuration
)

REM Setup database
echo [INFO] Setting up database...
python setup_database.py
if errorlevel 1 (
    echo [ERROR] Failed to setup database
    pause
    exit /b 1
)

REM Start server
echo.
echo [SUCCESS] Starting FastAPI server...
echo [INFO] Server will be available at: http://localhost:5001
echo [INFO] API Documentation: http://localhost:5001/docs
echo [INFO] Press Ctrl+C to stop the server
echo.

python main.py

pause