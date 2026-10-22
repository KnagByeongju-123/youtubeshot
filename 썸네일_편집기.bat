@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 썸네일 편집기
rem 사용법: 이 파일에 영상 콘텐츠 폴더(output\장문\00xx_제목)나 <제목>_썸네일_편집.json 을 끌어다 놓기.
rem        그냥 실행하면 빈 편집기가 열리고, 위쪽 '📂 영상 폴더 열기'로 고를 수 있음.
py -3.11 -X utf8 썸네일_편집기.py %1
if errorlevel 1 pause
