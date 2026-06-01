#!/bin/bash
# run_mumble_chat.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"

if [ ! -f "$VENV/bin/python" ]; then
    echo "venv not found. Run setup_mumble_chat.sh first."
    exit 1
fi

# ── Yggdrasil lifecycle ───────────────────────────────────────────────────────
# Start if not running; never stop on exit — yggdrasil is a system service
# and other sessions or apps may depend on it staying up.

if command -v systemctl &>/dev/null && \
   systemctl list-unit-files yggdrasil.service &>/dev/null 2>&1; then
    if ! systemctl is-active --quiet yggdrasil; then
        echo "Starting Yggdrasil…"
        sudo systemctl start yggdrasil

        printf "Waiting for Yggdrasil interface"
        for i in $(seq 1 20); do
            if ip link show ygg0 &>/dev/null 2>&1 || \
               ip link show tun0 &>/dev/null 2>&1; then
                echo " — ready."
                break
            fi
            printf "."
            sleep 1
        done
        [[ $i -eq 20 ]] && echo " — timeout, continuing anyway."
    fi
fi

# ── Launch ────────────────────────────────────────────────────────────────────

"$VENV/bin/python" "$SCRIPT_DIR/mumble_chat.py" "$@"
