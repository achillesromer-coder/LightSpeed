@echo off
setlocal
cd /d "%~dp0\.."
python tools\run_ls_go_bridge.py
endlocal
