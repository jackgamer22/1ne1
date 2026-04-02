@echo off
echo [MagxxxicVot SMS XII V6] Starting sender...

REM Default environment variables (can be edited by user)
set SMS_API_SERVICE=textbelt
set SMS_API_KEY=textbelt
set SMS_SENDER_ID=
set SMS_DELAY=1.0

python sms_sender.py
pause
