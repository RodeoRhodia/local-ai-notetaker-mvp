#!/usr/bin/env bash
# Launch the capture with Windows Python from a WSL shell.
cd "$(dirname "$0")" || exit 1
exec python.exe capture.py "$@"
