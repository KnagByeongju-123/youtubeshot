@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Pick a thumbnail - click one of the candidates
if "%~1"=="" goto usage
py -3.11 -X utf8 소재탐색\thumb_pick.py %*
echo.
pause
exit /b

:usage
echo 사용법: 썸네일 후보가 있는 폴더를 이 파일 위에 끌어다 놓으세요.
echo   - 소재탐색 소재 폴더: output\장문\_소재탐색\날짜\NN_이름
echo   - MP4 썸네일 폴더: 영상이름_썸네일_mp4
echo   - 영상의 _썸네일_후보 폴더: 프로그램 후보와 외부 후보를 한 화면에서
echo 고른 파일은 그 폴더의 썸네일_최종.jpg 로 저장됩니다.
echo 자동으로 고르려면: 썸네일_고르기.bat 폴더 --자동
echo.
pause
exit /b 1
