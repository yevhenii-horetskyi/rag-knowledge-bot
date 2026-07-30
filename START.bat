@echo off
cd /d "%~dp0"
echo ============================================
echo    RAG Knowledge Bot
echo ============================================
echo.
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    echo IMPORTANT: check "Add Python to PATH" during install.
    pause
    exit /b
)
if not exist "venv\" (
    echo First run - preparing environment, please wait...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
echo.
echo Starting the bot...
echo.
python -m src.bot
echo.
echo Bot stopped. Press any key to exit.
pause >nul
