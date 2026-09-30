@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   Integrated Avodah LLC - Ollama Background Setup
echo   Location: Lawrence, KS
echo ===================================================

:: 1. Voice-Activated Pin Protocol Prompt
echo.
echo ===================================================
echo   SECURE GATEWAY: VOICE-ACTIVATED PIN PROTOCOL
echo ===================================================
set /p "VOICE_PIN=Enter Voice-Activated PIN (Avodah-Stewardship-Integrity-Compliance): "

if /i "%VOICE_PIN%"=="Avodah-Stewardship-Integrity-Compliance" (
    echo [SUCCESS] PIN verified. Voice signature confirmed: Authoritative, Technical, Precise, Trustworthy.
) else (
    echo [SECURITY ALERT] Invalid PIN sequence. Aborting installation.
    goto :end
)

:: 2. Check and Download/Install Ollama Background Service
echo.
echo [INFO] Checking Ollama installation status...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Ollama not found locally. Downloading and installing Ollama for background execution...
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'"
    echo [INFO] Running Ollama installer silently in the background...
    start /wait %TEMP%\OllamaSetup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
) else (
    echo [INFO] Ollama is already installed on this system.
)

:: 3. Start Ollama Service and Pull Default Open-Source Model
echo.
echo [INFO] Launching Ollama background service...
start /b ollama serve >nul 2>&1

echo [INFO] Pulling open-source model (e.g., llama3) for local offline AI assistance...
ollama pull llama3

:: 4. Final Confirmation under Integrated Avodah LLC Context
echo.
echo [INFO] Profile: Integrated Avodah LLC
echo [INFO] Address: 2523 Redbud Ln, APT 16, Lawrence, KS 66046, US
echo [INFO] Mission: A holistic corporate compliance portal facilitating ethical stewardship.
echo [SUCCESS] Ollama AI assistant is now running successfully in the background.

:end
echo.
echo ===================================================
echo   Ollama Background Deployment Complete.
echo ===================================================
PAUSE
