@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Vosk API server...
python\python.exe -m poetry run uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause 