@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 goto :no_python
  set "PYTHON_CMD=python"
)

set "PYTHONPATH=%CD%\src"
%PYTHON_CMD% -m seo_autopilot.local_install
if errorlevel 1 goto :fail

echo.
echo SEO Autopilot 1.5.0 installed locally without network access.
echo Open the website repository in Codex and request an SEO audit.
echo You can also run: seo-autopilot doctor .
echo If that command is not found, add the Python user Scripts directory shown above to PATH.
echo.
pause
exit /b 0

:no_python
echo ERROR: Python 3.10 or newer was not found.
pause
exit /b 1

:fail
echo.
echo Installation stopped safely. No project repository was modified.
pause
exit /b 1
