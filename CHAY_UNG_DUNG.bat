@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [LOI] Ung dung chua duoc cai dat. Hay chay CAI_DAT.bat truoc.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python app.py
if errorlevel 1 pause
