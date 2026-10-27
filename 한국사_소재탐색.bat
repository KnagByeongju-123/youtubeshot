@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Korean history mystery topic finder (free)
echo 한국사 미스터리 소재 탐색: 한국어 뉴스(구글 뉴스)·해외 논문(OpenAlex)·유튜브 인기 조사로 소재를 찾아
echo output\장문\_소재탐색\ 에 리포트와 기획메모를 만듭니다. 무료. 옵션: --days 365 --편수 15 --주제목록 3 --no-youtube
echo.
py -3.11 -X utf8 한국사_소재탐색.py %*
echo.
pause
