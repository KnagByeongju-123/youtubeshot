@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Latest discovery finder - recent journal and news discoveries for the true-story batch
echo 최근 90일 저널·뉴스에서 '새로 밝혀진 과학 발견'을 찾아 실화_주제목록.txt 에 추가합니다 (최신일수록 우대).
echo 소재별 기획메모, 썸네일 3안, 해시태그를 output\장문\_소재탐색\ 에 만듭니다. 무료.
echo 끝나면 실화_연속제작.bat 을 실행하세요. 옵션: --편수 5 --days 90 --목록만 --규칙제목
echo.
py -3.11 -X utf8 실화_소재탐색.py --발견 %*
echo.
pause
