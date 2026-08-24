@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 prepare_editions.py --build-zips
) else (
  python prepare_editions.py --build-zips
)
if errorlevel 1 (
  echo.
  echo Build stopped safely. Review the error above.
  echo Existing unmarked or manually modified output is never overwritten without --force.
  pause
  exit /b 1
)
echo.
echo Transparent User and Engineering editions are ready in user, engineering and dist.
pause
