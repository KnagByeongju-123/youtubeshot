@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Re-render all videos in output with male voice 2 (Supertonic M2)
echo output\장문 의 모든 영상을 남자 성우 2(Supertonic M2), 배경음 거의 없음으로 다시 만듭니다.
echo 시작 전에 목록을 보여주고 물어봅니다. 특정 영상만: 성우2로_다시만들기.bat --only 인더스
echo.
py -3.11 -X utf8 성우2로_다시만들기.py %*
echo.
pause
