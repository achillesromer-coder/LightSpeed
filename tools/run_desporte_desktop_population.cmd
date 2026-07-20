@echo off
setlocal
set "REPO_ROOT=%~dp0.."

echo Running bounded De Sporte to LightSpeed Desktop population...
echo.
py -3 "%REPO_ROOT%\scripts\populate_desporte_desktop.py"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo De Sporte Desktop population requires review.
  echo Expected receipts are under the canonical LightSpeed Runtime exports\agent_home folder.
  exit /b %EXIT_CODE%
)

echo.
echo De Sporte Desktop population completed.
echo Open LightSpeed Desktop and verify the De Sporte runtime panel before accepting soft-launch completion.
exit /b 0
