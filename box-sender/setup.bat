@echo off
echo --- Box Sender Setup ---
pip install -r requirements.txt
playwright install chromium
echo.
echo Setup complete. You can now run start.bat
pause
