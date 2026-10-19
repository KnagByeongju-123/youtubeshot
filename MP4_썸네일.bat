@echo off
chcp 65001 >nul
cd /d "%~dp0"
title MP4 thumbnail - pick scenes from a finished video and build thumbnail candidates (free, local)
if "%~1"=="" (
  echo 사용법: 이 파일 위에 MP4 를 끌어다 놓거나,  MP4_썸네일.bat "영상.mp4" [--상태 "가설 제안"] [--소재명 "달의 두 얼굴"] [--후보폴더]
  echo 결과: ^<영상 폴더^>\^<영상이름^>_썸네일_mp4\  (후보 5장 + 후보_모음표.jpg + meta.json)
  pause
  exit /b 1
)
py -3.11 -X utf8 소재탐색\mp4_thumbs.py %*
echo.
pause
