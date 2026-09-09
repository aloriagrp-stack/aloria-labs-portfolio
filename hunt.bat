@echo off
setlocal
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers

python hunt.py %*

if "%~1"=="" pause
