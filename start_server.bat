@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================================
echo                    XiaoHongShu ToolBox Web Server
echo ================================================================
echo.
echo Starting server, please wait...
echo.

python environment/server.py

echo.
echo Server closed, press any key to exit...
pause >nul