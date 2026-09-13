@echo off
setlocal
if not defined LIGHTSPEED_CANONICAL_ROOT set "LIGHTSPEED_CANONICAL_ROOT=D:\LightSpeed"
set "RECEIPT=%LIGHTSPEED_CANONICAL_ROOT%\App\Z Axis\Z-4_Merovingian\data\runtime_exports\cognigrex_local_stack_receipt.json"
if not defined LIGHTSPEED_PYTHON set "LIGHTSPEED_PYTHON=%LIGHTSPEED_CANONICAL_ROOT%\Environment\Scripts\python.exe"

echo Starting the bounded local Cognigrex stack...
echo Components: Merovingian, LS GO bridge, LightSpeed Desktop.
echo Web, publication, destructive cleanup and workbook mutation remain disabled.
echo.

"%LIGHTSPEED_PYTHON%" "%LIGHTSPEED_CANONICAL_ROOT%\Automation\run_cognigrex_local_stack.py" --skip-desporte-population --json-output "%RECEIPT%"
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
