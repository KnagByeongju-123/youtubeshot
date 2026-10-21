@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Make thumbnail candidates for every video
echo output\장문 영상마다 썸네일 후보(디자인 16가지 + 영상 장면)를 새로 만듭니다. 영상과 지금 유튜브 썸네일은 그대로입니다.
echo 특정 영상만: 썸네일_후보_만들기.bat --only 나스카
echo.
py -3.11 -X utf8 썸네일_후보_만들기.py %*
echo.
pause
