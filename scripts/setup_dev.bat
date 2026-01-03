@echo off
REM Development setup script for Windows
REM Run as Administrator or with Developer Mode enabled

echo CADHY Development Setup for Windows
echo ====================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Run Python setup script
python "%SCRIPT_DIR%setup_dev.py" %*

if errorlevel 1 (
    echo.
    echo Setup failed. You may need to:
    echo 1. Run this script as Administrator, or
    echo 2. Enable Developer Mode in Windows Settings
    echo.
    pause
)
