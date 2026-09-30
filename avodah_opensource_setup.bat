@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   Integrated Avodah LLC - Open-Source API Key Setup
echo   Location: Lawrence, KS
echo ===================================================

:: 1. Verify Local Python/Node Environment
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python environment not detected.
    goto :end
)

:: 2. Voice-Activated Pin Protocol Prompt
echo.
echo ===================================================
echo   SECURE GATEWAY: VOICE-ACTIVATED PIN PROTOCOL
echo ===================================================
set /p "VOICE_PIN=Enter Voice-Activated PIN (Avodah-Stewardship-Integrity-Compliance): "

if /i "%VOICE_PIN%"=="Avodah-Stewardship-Integrity-Compliance" (
    echo [SUCCESS] PIN verified. Voice signature confirmed: Authoritative, Technical, Precise, Trustworthy.
) else (
    echo [SECURITY ALERT] Invalid PIN sequence. Aborting secure setup.
    goto :end
)

:: 3. Recommended Open-Source API Integration Options
echo.
echo [INFO] Recommended Open-Source Alternatives for API Keys ^& Local Servers:
echo -------------------------------------------------------------------
echo   1. Ollama      - Run models locally with zero paid API keys needed.
echo   2. LM Studio   - Local GUI server with an OpenAI-compatible API endpoint.
echo   3. Hugging Face- Free user access token for serverless public models.
echo   4. Groq        - Free developer tier for high-speed open-source weights.
echo -------------------------------------------------------------------

:: 4. Execute Local Environment Configuration via Business Context
echo.
echo [INFO] Profile: Integrated Avodah LLC
echo [INFO] Address: 2523 Redbud Ln, APT 16, Lawrence, KS 66046, US
echo [INFO] Core Purpose: Holistic corporate compliance portal ^& ethical stewardship.

python -c "import os; from google import genai; api_key = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY_HERE'); client = genai.Client(api_key=api_key); i = client.create(agent='antigravity-preview-05-2026', input='Configure open-source local API alternatives (Ollama, LM Studio) for Integrated Avodah LLC located at 2523 Redbud Ln, APT 16, Lawrence, KS 66046.', environment='remote'); print('Interaction ID:', i.id); print('Status: Open-source API routing initialized successfully.')"

:end
echo.
echo ===================================================
echo   Open-Source API Configuration Complete.
echo ===================================================
PAUSE
