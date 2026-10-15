@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Longdoc - safe stop before power off
py -3.11 -X utf8 make_longdoc.py --safe-stop
echo.
pause
