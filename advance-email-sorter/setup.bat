@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo        MAGXXICVOX ADVANCE EMAIL SORTER SETUP
echo ========================================================

:: Check for GCC
where gcc >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] GCC is not installed. Please install MinGW-w64 or another C compiler.
    pause
    exit /b 1
)

:: Check for Make
where make >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] 'make' is not installed. Using direct GCC command.
    echo Compiling...
    gcc -Wall -Wextra -pthread -o email_sorter main.c
) else (
    echo [INFO] 'make' detected. Compiling using Makefile...
    make clean >nul 2>nul
    make
)

if %errorlevel% equ 0 (
    echo ========================================================
    echo [SUCCESS] Email Sorter has been compiled successfully.
    echo.
    echo To start the sorter, run: email_sorter.exe [input] [output]
    echo ========================================================
) else (
    echo [ERROR] Compilation failed.
)

pause
