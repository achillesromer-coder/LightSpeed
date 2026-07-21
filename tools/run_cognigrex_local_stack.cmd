@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "RECEIPT=%REPO_ROOT%\desktop\LightSpeed_Runtime\exports\agent_home\cognigrex_local_stack_receipt.json"
if not defined LIGHTSPEED_PYTHON set "LIGHTSPEED_PYTHON=%REPO_ROOT%\venv\Scripts\python.exe"

echo Starting the bounded local Cognigrex stack...
echo Components: De Sporte population, Merovingian, LS GO bridge, LightSpeed Desktop.
echo Web, publication, destructive cleanup and workbook mutation remain disabled.
echo.

"%LIGHTSPEED_PYTHON%" "%REPO_ROOT%\scripts\run_cognigrex_local_stack.py" --json-output "%RECEIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
  echo Local Cognigrex stack passed its startup checks.
) else (
  echo Local Cognigrex stack requires review.
)
echo Receipt:
echo   %RECEIPT%
exit /b %EXIT_CODE%
