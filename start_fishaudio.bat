@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo   Launching M.I.K.O. [Fish Audio S2.1 Pro Free]
echo ========================================================

:: Verify virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at venv\Scripts\python.exe
    echo Please run setup.bat first to set up the project environment.
    echo ========================================================
    pause
    exit /b 1
)

:: Check if Ollama is running, and start it if needed
curl.exe -s http://127.0.0.1:11434/api/tags > nul 2>&1
if errorlevel 1 (
    echo Starting Ollama server...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start /min "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    ) else (
        start /min "" ollama serve
    )
    ping -n 3 127.0.0.1 > nul
)

:: Check if Unity audio server is running on port 8000, and start it if needed
curl.exe -s http://127.0.0.1:8000/audio_status > nul 2>&1
if errorlevel 1 (
    echo Starting Unity audio server [app.py]...
    start "OneReality Audio Server" /min cmd /k "venv\Scripts\python.exe app.py"
    ping -n 2 127.0.0.1 > nul
)

:: Start the Desktop Application if present
if exist "Miko_desktop\Miko_desktop.exe" (
    start "" "Miko_desktop\Miko_desktop.exe"
)

:: Start the main Python script with Fish Audio S2.1 Pro
venv\Scripts\python.exe Miko_FishAudio.py
if errorlevel 1 (
    echo.
    echo ========================================================
    echo Application exited with an error. See traceback above.
    echo Check crash.log for full details.
    echo ========================================================
    pause
)
