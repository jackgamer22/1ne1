@echo off
echo Setting up Email Verifier...

REM Check if Python is installed and in PATH
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not found in PATH. Please install Python and add it to your PATH.
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not installed or not found in PATH. Please ensure pip is installed with Python.
    pause
    exit /b 1
)

REM Create a virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Create necessary directories if they don't exist (relative to the script location)
echo Creating directories if they don't exist...
if not exist uploads mkdir uploads
if not exist output mkdir output

echo Setup complete. Starting Flask server...
echo You can access the application at http://localhost:5000 (or this machine's IP on port 5000)
echo Press Ctrl+C to stop the server.

REM Run the Flask application (assuming app.py is in the backend folder)
python backend/app.py

echo Deactivating virtual environment...
call .venv\Scripts\deactivate.bat

pause
