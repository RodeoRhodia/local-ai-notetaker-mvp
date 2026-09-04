#!/usr/bin/env bash
# Launch the notetaker with Windows Python from a WSL shell.
cd "$(dirname "$0")" || exit 1
exec python.exe notetaker.py "$@"
