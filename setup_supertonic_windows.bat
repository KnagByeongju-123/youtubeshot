@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto :path_error

echo =====================================================
echo Supertonic 3 - Windows 11 installer [ASCII SAFE]
echo BasicBook N95, 8GB RAM - local voice generation
echo =====================================================
echo Install directory: %CD%
echo.

py -3.11 --version >nul 2>&1
if errorlevel 1 goto :missing_py

if exist ".supertonic_venv\Scripts\python.exe" goto :venv_ready
echo [1/4] Creating isolated Python environment...
py -3.11 -m venv ".supertonic_venv"
if errorlevel 1 goto :failed

:venv_ready
set "VPY=%CD%\.supertonic_venv\Scripts\python.exe"
echo [2/4] Installing voice engine and download tool...
"%VPY%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :failed
"%VPY%" -m pip install --disable-pip-version-check "https://github.com/supertone-oss-archive/supertonic-py/archive/df0f9686dac7fbbde391b759e2ee5286a3737622.zip" "huggingface_hub[cli]"
if errorlevel 1 goto :failed

if not exist ".supertonic_venv\Scripts\hf.exe" goto :missing_hf
if not exist "supertonic_assets\onnx\text_encoder.onnx" goto :download
if not exist "supertonic_assets\onnx\vector_estimator.onnx" goto :download
if not exist "supertonic_assets\onnx\vocoder.onnx" goto :download
if not exist "supertonic_assets\voice_styles\M1.json" goto :download
goto :model_ready

:download
echo [3/4] Downloading the free model, approx. 415 MB...
".supertonic_venv\Scripts\hf.exe" download supertone-oss-archive/supertonic-3 --revision aafc6e32416a594460b32413efc49d7fe4ce6d46 --local-dir "supertonic_assets"
if errorlevel 1 goto :failed

:model_ready
echo [+] Optional: OpenCV for faster video rendering (skipped if it fails)...
py -3.11 -m pip install --disable-pip-version-check opencv-python-headless
echo [+] Optional: rembg (AI cutout for thumbnails) + faster-whisper (narration check, English subtitles)...
py -3.11 -m pip install --disable-pip-version-check "rembg[cpu]" faster-whisper
echo [4/4] Generating a short voice test...
"%VPY%" "supertonic_voice_test.py" --voices M1 --moods neutral
if errorlevel 1 goto :failed

echo.
echo =====================================================
echo SUCCESS! Check voice_samples\M1_neutral.wav
echo Run the app: run_shorts_supertonic.bat
echo =====================================================
pause
exit /b 0

:missing_py
echo.
echo ERROR: Python 3.11 was not found.
echo Please install 64-bit Python 3.11 and then run this file again.
echo To see installed Python versions, run: py -0p
goto :failed

:missing_hf
echo.
echo ERROR: hf.exe was not installed in the virtual environment.
goto :failed

:path_error
echo ERROR: Cannot access the folder containing this BAT file.
goto :failed

:failed
echo.
echo ERROR: Setup did not finish. Please copy the LAST error lines.
echo Your original shorts_novel_maker.py was not modified.
pause
exit /b 1
