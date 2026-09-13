@echo off

:: Start Ollama in the background (minimized)
start /min cmd /c "ollama serve"

:: Start the Desktop Application
start "" "MITSUHA_DESKTOP\MITSUHA_DESKTOP.exe"

:: Start the main Python script
venv\Scripts\python.exe MITSUHAVR_Ollama.py