@echo off
chcp 65001 >nul
cd /d "%~dp0"
title True-story batch - AI picks real-event topics and makes 10-min docs one by one (pause: run the pause .bat)
py -3.11 -X utf8 make_longdoc.py --실화
echo.
pause
