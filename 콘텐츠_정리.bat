@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Organize finished videos into one folder per title
echo output\장문 의 완성된 영상을 제목별 폴더로 정리합니다 (영상 만드는 중이면 건너뜀).
echo.
py -3.11 -X utf8 콘텐츠_정리.py
echo.
pause
