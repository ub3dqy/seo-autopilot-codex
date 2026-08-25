#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m seo_autopilot.local_install
printf '\nSEO Autopilot 1.5.0 installed locally without network access.\nOpen the website repository in Codex and ask for an SEO audit, or run:\n  seo-autopilot doctor .\n  seo-autopilot audit .\n'
