@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "RECEIPT_DIR=%REPO_ROOT%\desktop\LightSpeed_Runtime\exports\agent_home"
set "RECEIPT_PATH=%RECEIPT_DIR%\desporte_soft_launch_receipt.json"

if not exist "%RECEIPT_DIR%" mkdir "%RECEIPT_DIR%"

py -3 "%REPO_ROOT%\scripts\validate_desporte_desktop_bridge.py" --require-local --json-output "%RECEIPT_PATH%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo De Sporte Desktop probe failed. Review:
  echo   %RECEIPT_PATH%
  exit /b %EXIT_CODE%
)

echo.
echo De Sporte Desktop probe passed.
echo Receipt:
echo   %RECEIPT_PATH%
echo.
echo Next local action:
echo   Regenerate the LightSpeed agent-home exports and confirm the De Sporte panel in Desktop.
exit /b 0
