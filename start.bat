@echo off
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
  echo Instala o Python 3 e marca "Add Python to PATH".
  pause
  exit /b 1
)
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist config.json (
  copy config.example.json config.json
  echo.
  echo Cole as chaves no config.json (openrouter_api_key / groq_api_key).
  echo Esse arquivo NAO vai pro GitHub.
  echo.
)
python main.py
if errorlevel 1 pause
