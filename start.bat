@echo off
chcp 65001 > nul

:: Check if Ollama is running, and start it if needed
curl.exe -s http://127.0.0.1:11434/api/tags > nul 2>&1
if errorlevel 1 (
    echo Starting Ollama server...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start /min "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    ) else (
        start /min "" ollama serve
    )
    timeout /t 2 /nobreak > nul
)

:: Start the Desktop Application
if exist "Miko_desktop\Miko_desktop.exe" (
    start "" "Miko_desktop\Miko_desktop.exe"
)

:: Start Miko with local GPT-SoVITS
venv\Scripts\python.exe Miko.py
if errorlevel 1 (
    echo.
    echo ========================================================
    echo Application exited with an error. See traceback above.
    echo Check crash.log for full details.
    echo ========================================================
    pause
)