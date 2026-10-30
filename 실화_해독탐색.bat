@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Decipher finder - ancient scripts, inscriptions and codes for the true-story batch
echo 최근 1년 저널·뉴스에서 '못 읽던 고대 문자·비문·암호를 읽어 낸 이야기'를 찾아 실화\주제목록.txt 에 추가합니다.
echo (채널에서 반응이 좋았던 쿠샨 문자·선형 엘람 문자 같은 소재) 소재별 기획메모, 썸네일 3안, 해시태그를 만듭니다. 무료.
echo 끝나면 실화_연속제작.bat 을 실행하세요. 옵션: --편수 5 --days 365 --목록만 --규칙제목
echo.
py -3.11 -X utf8 실화_소재탐색.py --해독 %*
echo.
pause
