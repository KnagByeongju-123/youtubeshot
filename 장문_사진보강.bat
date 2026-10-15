@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Longdoc maker - adding more photos (pause: run the pause .bat)
py -3.11 -X utf8 make_longdoc.py --more-photos
echo.
pause
