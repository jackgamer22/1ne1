@echo off
echo Starting Bulk Emailer VictorV3 Application...
echo ============================================

set VENV_NAME=venv
set SCRIPT_DIR=%~dp0

REM Check if virtual environment exists
if not exist "%SCRIPT_DIR%%VENV_NAME%\Scripts\activate.bat" (
    echo Virtual environment '%VENV_NAME%' not found in %SCRIPT_DIR%.
    echo Please run setup.bat first to create the virtual environment and install dependencies.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "%SCRIPT_DIR%%VENV_NAME%\Scripts\activate.bat"

REM Check if app.py exists
if not exist "%SCRIPT_DIR%app.py" (
    echo app.py not found in %SCRIPT_DIR%.
    echo Ensure the script is run from the root directory of the application.
    pause
    exit /b 1
)

REM Start the Flask application
echo Starting Flask application (app.py)...
echo You can access the application at http://localhost:5000 (or your machine's IP).
echo Press Ctrl+C in this window to stop the server.
python "%SCRIPT_DIR%app.py"

echo Flask application stopped.
pause
exit /b 0
