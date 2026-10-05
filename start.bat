@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
start "" http://127.0.0.1:8765
.venv\Scripts\python.exe server.py %*
pause
exit /b
:failed
echo Setup failed. Install Python 3.11 or newer with the Python launcher, then try again.
pause
exit /b 1
