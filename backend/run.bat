@echo off
REM Backend Setup and Run Script for Resume Generator (Windows)

echo ==================================
echo Resume Generator - Backend Setup
echo ==================================
echo.

REM Navigate to backend directory
cd /d "%~dp0"

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo.

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

echo.

REM Install dependencies
echo [SETUP] Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==================================
echo [OK] Setup Complete!
echo ==================================
echo.
echo Starting Flask server...
echo.

REM Run the Flask application
python app.py

pause
