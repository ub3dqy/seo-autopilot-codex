@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\verify_local.py
) else (
  python scripts\verify_local.py
)
if errorlevel 1 (
  echo.
  echo Local verification FAILED.
  echo Review local-verification\latest.log and local-verification\latest.json.
  pause
  exit /b 1
)
echo.
echo Local verification PASSED.
echo Evidence: local-verification\latest.json
pause
