@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Longdoc batch - AI picks popular topics and makes them one by one (pause: run the pause .bat)
py -3.11 -X utf8 make_longdoc.py --batch
echo.
pause
