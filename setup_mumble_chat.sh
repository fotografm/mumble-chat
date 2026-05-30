#!/bin/bash
# setup_mumble_chat.sh — sets up mumble_chat.py in a venv
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"

echo "=== Mumble Chat Setup ==="

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install it: sudo apt install python3"
    exit 1
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "tkinter not found — installing..."
    sudo apt-get install -y python3-tk
fi

echo "Creating virtual environment..."
python3 -m venv "$VENV"

echo "Installing pymumble v2 from Codeberg (Python 3.12 compatible)..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install "git+https://codeberg.org/pymumble/pymumble.git"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Run with:"
echo "  $SCRIPT_DIR/run_mumble_chat.sh"
echo ""
echo "Or with arguments:"
echo "  $SCRIPT_DIR/run_mumble_chat.sh --host <server_ygg_addr> --user <yourname>"
echo ""
