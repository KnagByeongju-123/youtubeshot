@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Topic finder - free search of journals/news, adds topics + briefs + thumbnails for the true-story batch
echo 실화 소재 탐색: 주요 과학저널·뉴스에서 '풀리지 않던 수수께끼' 연구를 찾아 실화_주제목록.txt 에 추가하고
echo 소재별 기획메모·썸네일 3안·해시태그를 output\장문\_소재탐색\ 에 만듭니다 (무료).
echo   끝나면 실화_연속제작.bat 을 실행하세요. 옵션: --편수 5 --days 180 --bg-commons --목록만 --규칙제목
echo.
py -3.11 -X utf8 실화_소재탐색.py %*
echo.
pause
