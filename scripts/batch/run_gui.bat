@echo off
setlocal
REM Navigate to repository root and call the PowerShell launcher
set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_gui.ps1"
endlocal
