@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" py -3 -m venv venv
if not exist "venv\Scripts\python.exe" (
 echo Python could not be started. Install Python 3.12 or newer.
 pause
 exit /b 1
)
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
 pause
 exit /b 1
)
echo Open http://localhost:5000 in your browser. Keep this window open while testing.
"venv\Scripts\python.exe" app.py
pause
