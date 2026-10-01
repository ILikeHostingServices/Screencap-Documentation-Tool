@echo off
REM Run-Screencap-GUI.bat
REM 2026-10-01
REM Version: v1.0.0
REM
REM PURPOSE:
REM Double-click launcher for the Screencap Documentation Tool GUI on Windows.
REM Starts screencap_gui.pyw without leaving a console window open.

setlocal
cd /d "%~dp0"

where pyw >nul 2>&1
if %ERRORLEVEL%==0 (
    start "" pyw -3 "%~dp0screencap_gui.pyw"
    exit /b 0
)
where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
    start "" pythonw "%~dp0screencap_gui.pyw"
    exit /b 0
)
echo Python 3 was not found. Run Install-Prerequisites.ps1 or install it with:
echo   winget install --id Python.Python.3.12 -e
pause
exit /b 2
