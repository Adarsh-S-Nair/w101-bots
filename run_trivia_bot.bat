@echo off
echo Starting Wizard101 Trivia Bot...
cd /d "%~dp0"

if not exist venv\Scripts\activate.bat (
    echo Virtual environment not found! Please make sure venv exists.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py --type trivia

if errorlevel 1 (
    echo.
    echo Bot encountered an error.
)

pause

