@echo off
echo [MagxxxicVot SMS XII V6] Starting sender...

REM Edit these or set them as environment variables
if "%SMS_API_SERVICE%"=="" set SMS_API_SERVICE=textbelt
if "%SMS_API_KEY%"=="" set SMS_API_KEY=
if "%SMS_SENDER_ID%"=="" set SMS_SENDER_ID=
if "%SMS_DELAY%"=="" set SMS_DELAY=1.0

python sms_sender.py
pause
