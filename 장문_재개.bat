@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.11 -X utf8 make_longdoc.py --resume
timeout /t 5