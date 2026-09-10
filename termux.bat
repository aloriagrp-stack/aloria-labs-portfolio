@echo off
setlocal
cd /d "%~dp0"
set PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers

echo.
echo ================================================================
echo   HUNTER MOBILE TERMUX SERVER (100% PURE TERMINAL - NO BROWSER)
echo ================================================================
echo.
python aloria-hunter\phone_terminal.py

pause
