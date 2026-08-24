@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install --user --upgrade --no-deps .
  if errorlevel 1 goto :fail
  py -3 -m seo_autopilot install-skill
  if errorlevel 1 goto :fail
) else (
  python -m pip install --user --upgrade --no-deps .
  if errorlevel 1 goto :fail
  python -m seo_autopilot install-skill
  if errorlevel 1 goto :fail
)
echo.
echo SEO Autopilot installed.
echo Open the website repository in Codex and request an SEO audit,
echo or run: seo-autopilot doctor .
echo.
pause
exit /b 0
:fail
echo.
echo Installation failed. Review the error above; no project repository was modified.
pause
exit /b 1
