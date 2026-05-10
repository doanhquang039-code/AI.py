@echo off
echo ========================================
echo   AI Virtual World - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python and Node.js are installed
echo.

REM Check if dependencies are installed
if not exist "frontend\node_modules\" (
    echo [INFO] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo.
)

REM Start Backend in new window
echo [INFO] Starting Backend API on port 8000...
start "AI Backend API" cmd /k "python -m uvicorn api.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

REM Start Frontend in new window
echo [INFO] Starting Frontend on port 4200...
start "AI Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo   Services Starting...
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend:     http://localhost:4200
echo.
echo Press any key to open browser...
pause >nul

REM Open browser
start http://localhost:4200

echo.
echo ========================================
echo   AI Virtual World is Running!
echo ========================================
echo.
echo To stop services:
echo   - Close the Backend and Frontend windows
echo   - Or press Ctrl+C in each window
echo.
pause
