#!/usr/bin/env bash
# Installer for macOS / Linux.  Usage:  bash install.sh
set -e
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
command -v "$PY" >/dev/null || { echo "python3 not found. Install Python 3.9+ first."; exit 1; }

if [ "$(uname)" = "Linux" ] && ! "$PY" -c "import tkinter" 2>/dev/null; then
  echo "tkinter missing (GUI needs it). Install it with one of:"
  echo "  Debian/Ubuntu : sudo apt install python3-tk python3-venv"
  echo "  Fedora        : sudo dnf install python3-tkinter"
  echo "  Arch          : sudo pacman -S tk"
  echo "Continuing — the CLI works without tkinter."
fi

"$PY" -m venv .venv 2>/dev/null || python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip -q
./.venv/bin/python -m pip install -r requirements.txt -q

echo
echo "Done."
echo "  GUI : ./.venv/bin/python tripo_app.py"
echo "  CLI : ./.venv/bin/python tripo_cli.py <url> -o ~/Downloads/tripo_dl"
