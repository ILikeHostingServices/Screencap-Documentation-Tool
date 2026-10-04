@echo off
REM Run-Screencap.bat
REM 2026-10-01
REM Version: v1.0.0
REM
REM PURPOSE:
REM Double-click launcher for screencap.py on Windows. Processes every video in
REM the source folder. Any extra arguments are passed through, for example:
REM   Run-Screencap.bat --threshold 0.003 --force

setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3 "%~dp0screencap.py" %*
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python 3 was not found. Run Install-Prerequisites.ps1 or install it with:
        echo   winget install --id Python.Python.3.12 -e
        set RC=2
        goto :end
    )
    python "%~dp0screencap.py" %*
)
set RC=%ERRORLEVEL%

:end
echo.
if "%RC%"=="0" (echo Finished successfully.) else (echo Finished with exit code %RC%. See output\screencap.log)
REM Keep the window open when launched by double-click
echo %CMDCMDLINE% | find /i "%~0" >nul && pause
exit /b %RC%
