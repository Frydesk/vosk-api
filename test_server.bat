@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Running test client...
python\python.exe -m poetry run python test_client.py

pause 