@echo off
REM Installation script for Minecraft HTTP Dual Protocol Server
REM Run this file to set up the server automatically

echo.
echo ========================================
echo Minecraft HTTP Dual Protocol Server
echo Setup Assistant
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo [OK] Python is installed

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the server:
echo   1. Run: venv\Scripts\activate.bat
echo   2. Run: python server.py
echo.
echo Then open: http://localhost:12505
echo.
echo To connect in Minecraft:
echo   - Server Address: localhost
echo   - Server Port: 12505
echo.
pause
