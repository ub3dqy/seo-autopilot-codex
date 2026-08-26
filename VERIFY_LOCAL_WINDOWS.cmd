@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -X utf8 scripts\verify_local_utf8.py %*
) else (
  python -X utf8 scripts\verify_local_utf8.py %*
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
