@echo off
title WhatsApp Web QR Login - Aloria Hunter
cls
cd /d "%~dp0\aloria-hunter"
set PLAYWRIGHT_BROWSERS_PATH=D:\playwright-browsers
python whatsapp_engine.py
pause
