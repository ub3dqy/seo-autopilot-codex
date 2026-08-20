#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 prepare_editions.py --build-zips
printf '\nUser and Engineering editions are ready in user/, engineering/ and dist/.\n'
