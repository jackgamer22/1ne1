@echo off
echo **********************************
echo *   MAGXXXICVOT B2B SNDR Setup   *
echo **********************************

echo.
echo [1/2] Installing dependencies...
python -m pip install rich PySocks requests defusedxml

echo.
echo [2/2] Setting up configuration...
if not exist config.json (
    echo Creating config.json from example...
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
