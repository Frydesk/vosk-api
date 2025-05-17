@echo off
echo Starting Vosk API server...
python -m poetry run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
pause 