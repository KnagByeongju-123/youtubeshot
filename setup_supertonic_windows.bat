@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
echo ===============================================================
echo   Supertonic 3 한국어 무료 성우 설치 (Windows 11 / 8GB RAM)
echo ===============================================================
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [설치 중단] 64비트 Python 3.11이 필요합니다.
  echo Python 3.11 설치 후 다시 이 파일을 실행하세요.
  goto :failed
)
if not exist ".supertonic_venv\Scripts\python.exe" (
  echo [1/3] 별도 Python 가상환경 생성...
  py -3.11 -m venv ".supertonic_venv"
  if errorlevel 1 goto :failed
)
set "PY=.supertonic_venv\Scripts\python.exe"
echo [2/3] 무료 AI 음성 패키지 설치...
"%PY%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :failed
rem 보관 저장소의 Supertonic 3 호환 SDK를 정확한 커밋으로 설치 (Git 불필요)
"%PY%" -m pip install --disable-pip-version-check "https://github.com/supertone-oss-archive/supertonic-py/archive/df0f9686dac7fbbde391b759e2ee5286a3737622.zip" "huggingface_hub[cli]"
if errorlevel 1 goto :failed
if not exist "supertonic_assets\onnx" (
  echo [3/3] Supertonic 3 모델 약 400MB 내려받는 중...
  ".supertonic_venv\Scripts\hf.exe" download supertone-oss-archive/supertonic-3 --revision aafc6e32416a594460b32413efc49d7fe4ce6d46 --local-dir "supertonic_assets"
  if errorlevel 1 goto :failed
) else (
  echo [3/3] 기존 모델 폴더를 사용합니다.
)
"%PY%" supertonic_voice_test.py --voices M1 --moods neutral
if errorlevel 1 goto :failed
echo.
echo [설치 및 기본 음성 테스트 성공] voice_samples 폴더를 확인하세요.
echo 프로그램: shorts_novel_maker_supertonic.py
pause
exit /b 0
:failed
echo.
echo [중단] 위 오류를 확인하세요. 프로그램 원본은 변경되지 않았습니다.
pause
exit /b 1
