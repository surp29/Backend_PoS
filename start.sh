#!/bin/bash
# PhanMemKeToan Backend Startup Script
# Professional FastAPI Backend Server

echo ""
echo "========================================"
echo "  PhanMemKeToan Backend Server"
echo "  Professional FastAPI Application"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found"
    echo "[INFO] Copying from env.example..."
    cp env.example .env
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to copy env.example"
        exit 1
    fi
    echo "[INFO] Please edit .env file with your configuration"
fi

# Setup database
echo "[INFO] Setting up database..."
python setup_database.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to setup database"
    exit 1
fi

# Start server
echo ""
echo "[SUCCESS] Starting FastAPI server..."
echo "[INFO] Server will be available at: http://localhost:5001"
echo "[INFO] API Documentation: http://localhost:5001/docs"
echo "[INFO] Press Ctrl+C to stop the server"
echo ""

python main.py