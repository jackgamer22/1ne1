@echo off
echo [MagxxxicVot SMS XII V6] Starting sender...

REM Note: Populating .env is recommended for security.
REM Environment variables can still be set here if necessary.
if "%SMS_API_SERVICE%"=="" set SMS_API_SERVICE=textbelt
if "%SMS_DELAY%"=="" set SMS_DELAY=1.0

python sms_sender.py
pause
