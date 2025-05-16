@echo off
setlocal enabledelayedexpansion

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Installing Poetry...
python -m pip install poetry

if errorlevel 1 (
    echo Error: Failed to install Poetry
    pause
    exit /b 1
)

echo Configuring Poetry...
python -m poetry config virtualenvs.in-project true
python -m poetry config virtualenvs.path .venv

echo Regenerating lock file...
python -m poetry lock --no-cache --regenerate

echo Installing dependencies with Poetry...
python -m poetry install --no-root

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Check if Vosk model exists
if exist "model" (
    echo Vosk model already exists.
) else (
    echo Downloading Vosk Spanish model...
    if exist "vosk-model-small-es-0.42.zip" (
        echo Vosk model archive already exists.
    ) else (
        powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; $url = 'https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip'; $output = 'vosk-model-small-es-0.42.zip'; Write-Host 'Downloading Vosk model...'; Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing}"
    )

    echo Extracting model...
    powershell -Command "& {Expand-Archive -Path 'vosk-model-small-es-0.42.zip' -DestinationPath '.' -Force}"

    echo Renaming model directory...
    if exist "model" rmdir /s /q "model"
    rename "vosk-model-small-es-0.42" "model"
)

REM Clean up only if we downloaded new files
if exist "vosk-model-small-es-0.42.zip" (
    echo Cleaning up Vosk model archive...
    del vosk-model-small-es-0.42.zip
)

echo Setup complete! You can now run start_server.bat to start the API server.
pause 