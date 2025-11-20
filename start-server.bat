@echo off
REM Resume Generator - Local Server Launcher (Windows)
REM This script starts a local web server for testing the application

echo ==================================
echo Resume Generator - Server Launcher
echo ==================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python found
    echo.
    echo Starting server on http://localhost:8000
    echo Press Ctrl+C to stop the server
    echo.
    echo Open your browser and navigate to:
    echo   - http://localhost:8000/QUICKSTART.html (Setup Guide)
    echo   - http://localhost:8000/index.html (Login Page)
    echo.
    python -m http.server 8000
    goto :end
)

REM Check if PHP is available
where php >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] PHP found
    echo.
    echo Starting server on http://localhost:8000
    echo Press Ctrl+C to stop the server
    echo.
    echo Open your browser and navigate to:
    echo   - http://localhost:8000/QUICKSTART.html (Setup Guide)
    echo   - http://localhost:8000/index.html (Login Page)
    echo.
    php -S localhost:8000
    goto :end
)

REM No server found
echo [ERROR] No suitable server found (Python or PHP required)
echo.
echo Please install Python or PHP to run this server.
echo Alternatively, you can:
echo   1. Install Node.js and run: npx http-server -p 8000
echo   2. Open index.html directly in your browser
echo.
pause
goto :end

:end
