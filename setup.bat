@echo off
echo ========================================================
echo   Setting up M.I.K.O. Environment
echo ========================================================

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo Installing PyAV binary...
venv\Scripts\python.exe -m pip install av --only-binary=av

echo Installing dependencies from requirements.txt...
venv\Scripts\python.exe -m pip install -r requirements.txt

if not exist ".env" (
    echo Creating .env from .env.example...
    copy ".env.example" ".env" > nul
    echo [NOTE] Remember to edit .env to add your API keys or adjust settings.
)

echo.
echo Running verification tests...
venv\Scripts\python.exe -m unittest test_refactor_clean.py
venv\Scripts\python.exe -m unittest test_fish_audio_integration.py

echo.
echo ========================================================
echo   Setup Complete!
echo   Launch with start.bat (GPT-SoVITS) or start_fishaudio.bat (Fish Audio)
echo ========================================================
pause