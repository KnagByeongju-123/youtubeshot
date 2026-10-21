@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Korean reading preview
echo 성우가 대본을 어떻게 읽을지 글로 미리 봅니다. 고칠 낱말은 읽기사전.txt 에 적으세요.
echo.
py -3.11 -X utf8 한국어_읽기.py %*
echo.
pause
