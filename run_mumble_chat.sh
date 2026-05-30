#!/bin/bash
# run_mumble_chat.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"

if [ ! -f "$VENV/bin/python" ]; then
    echo "venv not found. Run setup_mumble_chat.sh first."
    exit 1
fi

"$VENV/bin/python" "$SCRIPT_DIR/mumble_chat.py" "$@"
