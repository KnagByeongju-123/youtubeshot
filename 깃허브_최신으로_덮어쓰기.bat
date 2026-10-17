@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto :failed
title GitHub -> this folder (overwrite with latest)

set "REPO_URL=https://github.com/KnagByeongju-123/youtubeshot"
set "BRANCH=main"

echo =====================================================
echo  Overwrite THIS folder with the latest files on GitHub
echo  Folder : %CD%
echo  Source : %REPO_URL%  (branch %BRANCH%)
echo =====================================================
echo  Program files are replaced with the GitHub version.
echo  Your own files (output\, shorts_novel_config.json,
echo  models\, .venv folders, videos...) are NOT touched.
echo.

where git >nul 2>&1
if errorlevel 1 goto :zip_mode

:git_mode
echo [git found] Using git to sync...
if not exist ".git" (
    echo   First run: turning this folder into a git checkout...
    git init -q
    if errorlevel 1 goto :failed
)
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    git remote add origin "%REPO_URL%"
    if errorlevel 1 goto :failed
) else (
    git remote set-url origin "%REPO_URL%"
)
echo   Downloading latest from GitHub...
git fetch --depth=1 origin %BRANCH%
if errorlevel 1 goto :failed
echo   Overwriting program files with the GitHub version...
git reset --hard origin/%BRANCH% -q
if errorlevel 1 goto :failed
git branch -M %BRANCH% >nul 2>&1
git branch --set-upstream-to=origin/%BRANCH% %BRANCH% >nul 2>&1
echo.
echo DONE. This folder now matches GitHub (%BRANCH%).
git log -1 --date=format:"%%Y-%%m-%%d %%H:%%M" --format="  Latest: %%ad  %%s"
goto :done

:zip_mode
echo [git not found] Downloading ZIP from GitHub instead...
set "TMPZIP=%TEMP%\youtubeshot_%BRANCH%.zip"
set "TMPDIR=%TEMP%\youtubeshot_%BRANCH%_unzip"
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_URL%/archive/refs/heads/%BRANCH%.zip' -OutFile '%TMPZIP%'; Expand-Archive -Path '%TMPZIP%' -DestinationPath '%TMPDIR%' -Force"
if errorlevel 1 goto :failed
echo   Copying files over this folder...
robocopy "%TMPDIR%\youtubeshot-%BRANCH%" "%CD%" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :failed
del /q "%TMPZIP%" >nul 2>&1
rmdir /s /q "%TMPDIR%" >nul 2>&1
echo.
echo DONE. This folder now matches GitHub (%BRANCH%).
echo (Tip: install Git for Windows - https://git-scm.com/download/win - and this becomes faster.)
goto :done

:failed
echo.
echo FAILED. Check the internet connection and the message above.
echo If the folder is in use by a running program, close it and run again.
pause
exit /b 1

:done
echo.
pause
exit /b 0
