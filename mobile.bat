@echo off
setlocal
cd /d "%~dp0"
chcp 65001 > nul
set PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo.
echo ========================================================
echo   HUNTER MOBILE COMMAND SERVER (LOCAL PRIVATE ENGINE)
echo ========================================================
echo.
python aloria-hunter\mobile_server.py

pause
