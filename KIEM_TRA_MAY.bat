@echo off
chcp 65001 >nul
title Kiểm tra máy - Douyin AI Translator
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [LOI] Ung dung chua duoc cai dat. Hay chay CAI_DAT.bat truoc.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python kiem_tra_may.py
echo.
pause
