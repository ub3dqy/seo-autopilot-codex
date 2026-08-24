#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m pip install --user --upgrade --no-deps .
"$PYTHON_BIN" -m seo_autopilot install-skill
printf '\nSEO Autopilot installed. Open the website repository in Codex and ask for an SEO audit, or run:\n  seo-autopilot doctor .\n  seo-autopilot audit .\n'
