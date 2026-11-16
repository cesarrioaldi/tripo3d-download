#!/usr/bin/env sh
# Launch the GUI (macOS / Linux).  Usage: ./run.sh
cd "$(dirname "$0")" || exit 1
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python tripo_app.py
fi
exec python3 tripo_app.py
