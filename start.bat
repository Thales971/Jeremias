@echo off
cd /d "%~dp0"
title Jeremias
echo.
echo === JEREMIAS ===
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo Python NAO esta no PATH.
  echo Instala em https://www.python.org/downloads/
  echo e MARCA a caixa "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

python -c "import tkinter" 2>nul
if errorlevel 1 (
  echo Esse Python veio sem janela grafica (Tkinter).
  echo Desinstala o Python, instala de novo do python.org
  echo e deixa marcado "tcl/tk and IDLE".
  echo.
  pause
  exit /b 1
)

echo [1/3] ambiente
if not exist .venv (
  python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo Falhou criar a pasta .venv
  pause
  exit /b 1
)

echo [2/3] libs  ^(primeira vez demora um pouco^)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo pip falhou. Copia o erro acima.
  pause
  exit /b 1
)

if not exist config.json (
  copy config.example.json config.json >nul
  echo.
  echo Cole as chaves no config.json ^(openrouter_api_key / groq_api_key^).
  echo Esse arquivo NAO vai pro GitHub.
  echo.
)

echo [3/3] abrindo a janela do Jeremias...
echo.
.venv\Scripts\python.exe main.py
echo.
if errorlevel 1 (
  echo O Jeremias fechou com ERRO. Copia o texto acima e manda no chat.
) else (
  echo Janela fechada.
)
echo.
pause
