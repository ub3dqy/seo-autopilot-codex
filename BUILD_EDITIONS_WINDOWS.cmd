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
  echo Build failed. See the error above.
  pause
  exit /b 1
)
echo.
echo User and Engineering editions are ready in user, engineering and dist.
pause
