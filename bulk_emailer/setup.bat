@echo off
echo Bulk Emailer VictorV3 Setup Script
echo ===================================

REM Check for Python
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not found in PATH.
    echo Please install Python 3 (e.g., from https://www.python.org/downloads/) and ensure it's added to your PATH.
    pause
    exit /b 1
) else (
    echo Python found.
)

REM Check for pip
echo Checking for pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not installed or not found. This is unusual for modern Python installations.
    echo Please ensure your Python installation includes pip.
    pause
    exit /b 1
) else (
    echo pip found.
)

REM Virtual environment name
set VENV_NAME=venv

REM Check if virtual environment already exists
if exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Virtual environment '%VENV_NAME%' already exists. Skipping creation.
) else (
    echo Creating virtual environment '%VENV_NAME%'...
    python -m venv %VENV_NAME%
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please check your Python installation.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

REM Activate virtual environment and install requirements
echo Activating virtual environment and installing requirements...
call "%VENV_NAME%\Scripts\activate.bat"

echo Installing packages from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements. Please check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo Requirements installed successfully.

REM Initialize the database
echo Initializing the database...
python -c "from app import init_db; print('Attempting to initialize DB...'); init_db(); print('DB initialization process complete.')"
if %errorlevel% neq 0 (
    echo Failed to initialize the database. Check app.py and database configuration.
    pause
    REM Deactivating venv before exit on error might be good, but script exits anyway
    exit /b 1
)
echo Database initialized.

REM Deactivate virtual environment (optional, as script ends here)
REM call "%VENV_NAME%\Scripts\deactivate.bat"

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo To run the application:
echo 1. Open a new command prompt or activate the venv manually:
echo    cd /d "%~dp0"
echo    call %VENV_NAME%\Scripts\activate.bat
echo 2. Run the Flask application:
echo    python app.py
echo 3. Open your web browser and go to: http://localhost:5000 (or your machine's IP if accessing externally)
echo.
echo IMPORTANT:
echo - Configure your SMTP server details in 'sender.py' (the SMTP_SERVERS list) before sending emails.
echo - The default admin user is 'admin' with password 'admin'. Change this after logging in.
echo.
pause
exit /b 0
