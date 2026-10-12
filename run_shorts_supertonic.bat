@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto :failed
py -3.11 "shorts_novel_maker_supertonic.py"
if errorlevel 1 goto :failed
exit /b 0
:failed
echo.
echo App startup failed. Please copy the error message above.
pause
exit /b 1
