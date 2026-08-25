@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\verify_local.py --build
) else (
  python scripts\verify_local.py --build
)
if errorlevel 1 (
  echo.
  echo Verification or build FAILED.
  echo Review local-verification\latest.log and local-verification\latest.json.
  echo Existing unmarked or manually modified output is never overwritten.
  pause
  exit /b 1
)
echo.
echo Verified User and Engineering editions are ready in user, engineering and dist.
echo Evidence: local-verification\latest.json
pause
