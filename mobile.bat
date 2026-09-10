@echo off
setlocal
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers

echo.
echo ========================================================
echo   HUNTER MOBILE COMMAND SERVER (LOCAL PRIVATE ENGINE)
echo ========================================================
echo.
python aloria-hunter\mobile_server.py

pause
