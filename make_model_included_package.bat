@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto :failed
py -3.11 --version >nul 2>&1
if errorlevel 1 goto :missing_py
py -3.11 "make_model_included_package.py"
if errorlevel 1 goto :failed
pause
exit /b 0
:missing_py
echo ERROR: Python 3.11 not found. Install Python 3.11 (64-bit).
:failed
echo ERROR: Transfer ZIP was NOT made. Read the message above.
pause
exit /b 1
