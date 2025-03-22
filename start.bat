@echo off
title Lost City Drop Search

echo Checking for Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python first.
    pause
    exit /b 1
)

echo Checking for requirements...
pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo pip is not installed. Please ensure pip is installed with Python.
    pause
    exit /b 1
)

echo Installing requirements from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

echo Launching app.py...
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to launch app.py. Check if the file exists and there are no errors in the code.
    pause
    exit /b 1
)

pause