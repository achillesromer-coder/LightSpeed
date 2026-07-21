@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "RECEIPT=%REPO_ROOT%\desktop\LightSpeed_Runtime\exports\agent_home\merovingian_soft_launch_receipt.json"

echo Starting bounded Merovingian health, project and receipt supervisor...
echo Web, destructive cleanup and direct external execution remain disabled.
echo.

py -3 "%REPO_ROOT%\scripts\run_merovingian_soft_launch.py" --watch --interval 60 --json-output "%RECEIPT%"
exit /b %ERRORLEVEL%
