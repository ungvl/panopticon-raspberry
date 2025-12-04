@echo off
echo [INFO] Starting Panopticon...

:: Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please run setup.sh (via Git Bash) or set up venv manually first.
    pause
    exit /b 1
)

:: Activate venv and run
call venv\Scripts\activate.bat
python -m src.start_aw

:: Pause if it crashes so user can see error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%
    pause
)
