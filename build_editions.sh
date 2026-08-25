#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 scripts/verify_local.py --build "$@"
printf '\nVerified User and Engineering editions are ready in user/, engineering/ and dist/.\n'
printf 'Evidence: local-verification/latest.json\n'
