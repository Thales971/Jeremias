@echo off
setlocal
cd /d "%~dp0"
title Jeremias
echo.
echo === JEREMIAS ===
echo.

where python >nul 2>&1
if errorlevel 1 goto nopython

python -c "import tkinter" 2>nul
if errorlevel 1 goto notk

echo [1/3] ambiente
if not exist .venv python -m venv .venv
if not exist .venv\Scripts\python.exe goto novenv

echo [2/3] libs - primeira vez demora
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto pipfail

if not exist config.json copy config.example.json config.json >nul

echo [3/3] abrindo a janela do Jeremias...
echo.
.venv\Scripts\python.exe main.py
if errorlevel 1 goto crashed
echo Janela fechada.
goto end

:nopython
echo Python NAO esta no PATH.
echo Instala em https://www.python.org/downloads/
echo e MARCA a caixa Add python.exe to PATH.
goto endfail

:notk
echo Esse Python veio sem janela grafica Tkinter.
echo Desinstala o Python, instala de novo do python.org
echo e deixa marcado tcl/tk and IDLE.
goto endfail

:novenv
echo Falhou criar a pasta .venv
goto endfail

:pipfail
echo pip falhou. Copia o erro acima.
goto endfail

:crashed
echo.
echo O Jeremias fechou com ERRO. Copia o texto acima e manda no chat.
goto endfail

:endfail
echo.
pause
exit /b 1

:end
echo.
pause
exit /b 0
