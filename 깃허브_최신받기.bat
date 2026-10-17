@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo GitHub(youtubeshot) 최신본 받는 중...
git pull --ff-only origin main
if errorlevel 1 (
  echo.
  echo 받기 실패: 이 PC에서 고친 파일이 있으면 먼저 올리거나 되돌린 뒤 다시 실행하세요.
  echo  - 고친 파일 확인: git status
) else (
  echo 완료. 이제 최신 버전으로 작업할 수 있습니다.
)
pause
