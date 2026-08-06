@echo off
chcp 65001 >nul
title Cài đặt Douyin AI Translator
cd /d "%~dp0"
echo Dang kiem tra Python...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [LOI] Chua tim thay Python 3.11.
  echo Hay cai Python 3.11 64-bit tu python.org va chon Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo [LOI] Cai dat that bai. Kiem tra Internet va dung luong o dia.
  pause
  exit /b 1
)
echo.
echo Cai dat thanh cong. Hay chay CHAY_UNG_DUNG.bat
pause
