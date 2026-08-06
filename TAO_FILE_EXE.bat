@echo off
chcp 65001 >nul
title Tạo file EXE Douyin AI Translator
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [LOI] Hay chay CAI_DAT.bat truoc.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
pyinstaller --noconfirm --clean --windowed --onedir --name Douyin_AI_Translator --collect-all faster_whisper --collect-all ctranslate2 app.py
if errorlevel 1 (
  echo [LOI] Tao EXE that bai. Xem thong bao phia tren.
  pause
  exit /b 1
)
echo Tao EXE thanh cong trong thu muc dist\Douyin_AI_Translator
pause
