#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 scripts/verify_local.py "$@"
printf '\nLocal verification passed. Evidence: local-verification/latest.json\n'
