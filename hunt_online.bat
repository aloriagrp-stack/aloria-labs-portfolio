@echo off
title Aloria Hunter - Online Autonomous AI Host
cls
echo ======================================================================
echo             ALORIA HUNTER - AUTONOMOUS AGENT HOST ONLINE
echo ======================================================================
echo.
echo [1/2] Starting Python Local Backend Server on port 8000...
start "Aloria Hunter Backend" /b python aloria-hunter\mobile_server.py
timeout /t 3 >nul

echo [2/2] Launching Cloudflare Tunnel for Worldwide HTTPS Access...
echo.
echo ----------------------------------------------------------------------
echo  Your Hunter Dashboard is LIVE at:
echo  https://alorialabs.in/hunter
echo.
echo  Access Password: shriyansh0402
echo ----------------------------------------------------------------------
echo.
echo Cloudflare Tunnel starting below. Keep this window open while hunting!
echo.
aloria-hunter\cloudflared.exe tunnel --url http://localhost:8000
