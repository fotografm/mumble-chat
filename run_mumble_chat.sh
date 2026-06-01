#!/bin/bash
# run_mumble_chat.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"

if [ ! -f "$VENV/bin/python" ]; then
    echo "venv not found. Run setup_mumble_chat.sh first."
    exit 1
fi

# ── Yggdrasil lifecycle ───────────────────────────────────────────────────────

STARTED_YGGDRASIL=0

if command -v systemctl &>/dev/null && \
   systemctl list-unit-files yggdrasil.service &>/dev/null 2>&1; then
    if ! systemctl is-active --quiet yggdrasil; then
        echo "Starting Yggdrasil…"
        sudo systemctl start yggdrasil
        STARTED_YGGDRASIL=1

        # Wait for the network interface to come up (ygg0 on 0.5+, tun0 on 0.4.x)
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

cleanup() {
    if [ "$STARTED_YGGDRASIL" -eq 1 ]; then
        echo "Stopping Yggdrasil…"
        sudo systemctl stop yggdrasil
    fi
}
trap cleanup EXIT

# ── Launch ────────────────────────────────────────────────────────────────────

"$VENV/bin/python" "$SCRIPT_DIR/mumble_chat.py" "$@"
