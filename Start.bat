@echo off
echo ==========================================
echo Ground Control Hub - Windows Startup
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16 or higher
    pause
    exit /b 1
)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Starting Ground Control Hub...
echo Project directory: %SCRIPT_DIR%
echo.

REM Backend setup and start
echo ==========================================
echo Setting up Backend...
echo ==========================================

if not exist "backend" (
    echo ERROR: backend directory not found!
    echo Please make sure you are running this script from the project root directory
    pause
    exit /b 1
)

cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements if requirements.txt exists
if exist "requirements.txt" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Python dependencies
        pause
        exit /b 1
    )
)

REM Copy .env file if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env configuration file...
        copy .env.example .env
    )
)

REM Check if main.py exists
if not exist "main.py" (
    echo WARNING: main.py not found in backend directory
    echo Looking for alternative entry points...
    if exist "app.py" (
        set BACKEND_ENTRY=app.py
        echo Found app.py, using as entry point
    ) else if exist "server.py" (
        set BACKEND_ENTRY=server.py
        echo Found server.py, using as entry point
    ) else (
        echo ERROR: No backend entry point found (main.py, app.py, or server.py)
        pause
        exit /b 1
    )
) else (
    set BACKEND_ENTRY=main.py
)

REM Start backend server in background
echo Starting backend server with %BACKEND_ENTRY% in background...
start /b "" cmd /c "call venv\Scripts\activate.bat && python %BACKEND_ENTRY%"

REM Wait for backend to initialize
echo Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

REM Return to project root
cd /d "%SCRIPT_DIR%"

REM Frontend setup and start
echo ==========================================
echo Setting up Frontend...
echo ==========================================

if not exist "frontend" (
    echo ERROR: frontend directory not found!
    echo Please make sure you are running this script from the project root directory
    pause
    exit /b 1
)

cd frontend

REM Install npm dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
) else (
    echo Node.js dependencies already installed
)

REM Check for package.json and determine start command
if not exist "package.json" (
    echo ERROR: package.json not found in frontend directory
    pause
    exit /b 1
)

REM Check if start script exists in package.json
findstr /c:"\"start\"" package.json >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: No start script found in package.json
    echo Trying alternative commands...
    set FRONTEND_CMD=npm run dev
) else (
    set FRONTEND_CMD=npm start
)

REM Return to project root for final messages
cd /d "%SCRIPT_DIR%"

echo.
echo ==========================================
echo Ground Control Hub Started Successfully!
echo ==========================================
echo Backend:  http://127.0.0.1:8000 (running in background)
echo Frontend: Starting now...
echo.
echo NOTE: Backend is running in background
echo Use stop_ground_control.bat to stop all services
echo.
echo Troubleshooting:
echo - Ensure STM32 USB CDC drivers are installed
echo - Check Device Manager for connected devices
echo - Verify firewall settings for WebSocket connections
echo.

REM Start frontend server in current window (this will block)
echo Starting frontend development server with %FRONTEND_CMD%...
echo Press Ctrl+C to stop both frontend and backend servers
echo.
cd frontend
%FRONTEND_CMD%