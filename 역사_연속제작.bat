@echo off
chcp 65001 >nul
cd /d "%~dp0"
title History channel batch - real records (Joseon Annals, Records of the Three Kingdoms) vs dramas, one by one
echo 역사 채널: 역사\주제목록.txt 의 주제를 순서대로 '기록으로 보는 진짜 역사' 다큐로 만듭니다.
echo 진행 기록은 실화 연속 제작과 따로 저장됩니다. (일시정지: 장문_일시정지.bat)
echo.
py -3.11 -X utf8 make_longdoc.py --역사
echo.
pause
