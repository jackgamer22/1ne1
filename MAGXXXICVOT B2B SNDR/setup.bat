@echo off
echo **********************************
echo *   MAGXXXICVOT B2B SNDR Setup   *
echo **********************************

echo.
echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install rich PySocks requests defusedxml playwright htmlmin dkimpy

echo.
echo [2/3] Installing Playwright browsers...
python -m playwright install chromium

echo.
echo [3/3] Setting up configuration...
if not exist config.json (
    echo Creating initial config.json from example...
    copy config.example.json config.json
) else (
    echo config.json already exists.
)

echo.
echo **********************************
echo *        Setup Complete!         *
echo **********************************
echo.
pause
