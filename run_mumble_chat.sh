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

if command -v systemctl &>/dev/null && systemctl list-unit-files yggdrasil.service &>/dev/null; then
    if ! systemctl is-active --quiet yggdrasil; then
        echo "Starting Yggdrasil and waiting for connection…"
        sudo systemctl start yggdrasil
        STARTED_YGGDRASIL=1

        # Wait for at least one peer to appear (timeout 30s)
        CONNECTED=0
        for i in $(seq 1 30); do
            printf "  Waiting for peer… (%ds)\r" "$i"
            PEER_COUNT=$(sudo yggdrasilctl getPeers 2>/dev/null \
                | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    peers = d.get('peers', [])
    print(len([p for p in peers if p.get('uptime', 0) > 0]))
except Exception:
    print(0)
" 2>/dev/null || echo 0)
            if [ "$PEER_COUNT" -gt 0 ] 2>/dev/null; then
                CONNECTED=1
                break
            fi
            sleep 1
        done

        printf "\r\033[K"   # clear the progress line
        if [ "$CONNECTED" -eq 1 ]; then
            echo "Yggdrasil connected."
        else
            echo "Yggdrasil started — no peers yet, continuing anyway."
        fi
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
