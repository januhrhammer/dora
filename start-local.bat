@echo off
REM Quick start script for local development (Windows)

echo.
echo 🚀 Starting Medicine Tracker - Local Development
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11 or higher.
    pause
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 20 or higher.
    pause
    exit /b 1
)

echo 📦 Setting up Backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env >nul
    echo ⚠️  Please edit backend\.env with your email settings!
)

REM Start backend
echo Starting FastAPI backend on port 8000...
start "Medicine Tracker - Backend" cmd /k "venv\Scripts\activate.bat && uvicorn app.main:app --reload"

cd ..

echo.
echo 📦 Setting up Frontend...
cd frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing Node dependencies...
    npm install >nul 2>&1
)

REM Start frontend
echo Starting Svelte frontend on port 5173...
start "Medicine Tracker - Frontend" cmd /k "npm run dev"

cd ..

echo.
echo ✅ Development servers started!
echo ================================================
echo.
echo 📍 Frontend: http://localhost:5173
echo 📍 Backend API: http://localhost:8000
echo 📍 API Docs: http://localhost:8000/docs
echo.
echo Two new windows have opened for backend and frontend.
echo Close those windows to stop the servers.
echo.
pause
