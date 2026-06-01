#!/bin/bash
# setup_mumble_chat.sh — installs Mumble Chat and its dependencies
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"

echo ""
echo "┌─────────────────────────────────────┐"
echo "│       Mumble Chat  —  Setup         │"
echo "└─────────────────────────────────────┘"
echo ""

# ── Yggdrasil ────────────────────────────────────────────────────────────────

if command -v yggdrasil &>/dev/null; then
    # Already installed — show address if the daemon is running
    YGG_ADDR=$(yggdrasilctl getself 2>/dev/null \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('address',''))" \
        2>/dev/null || true)
    echo "  ✓ Yggdrasil is already installed."
    if [ -n "$YGG_ADDR" ]; then
        echo "    Your address: $YGG_ADDR"
    fi
    echo ""
else
    echo "  ──────────────────────────────────────────"
    echo "   Yggdrasil is not installed"
    echo "  ──────────────────────────────────────────"
    echo ""
    echo "  Mumble Chat is designed to connect to Mumble servers over"
    echo "  Yggdrasil — a free, encrypted, peer-to-peer IPv6 network."
    echo ""
    echo "  Without Yggdrasil you can only reach Mumble servers on the"
    echo "  regular internet (by hostname or public IP address)."
    echo "  With Yggdrasil you can reach any Mumble server anywhere on"
    echo "  the Yggdrasil network without opening firewall ports."
    echo ""
    echo "  Would you like to install Yggdrasil now?"
    echo "  (Requires sudo / administrator access)"
    echo ""
    read -r -p "  Install Yggdrasil? [y/N] " yn
    echo ""

    case "$yn" in
        [Yy]*)
            if ! command -v apt-get &>/dev/null; then
                echo "  Automatic install only works on Debian / Ubuntu / Mint."
                echo "  Please install Yggdrasil manually, then re-run this script:"
                echo "    https://yggdrasil-network.github.io/installation.html"
                echo ""
                read -r -p "  Continue without Yggdrasil? [y/N] " cont
                [[ "$cont" =~ ^[Yy] ]] || { echo "Exiting."; exit 0; }
            else
                echo "  Installing Yggdrasil via the official apt repository …"
                echo ""

                # Ensure gpg is available
                if ! command -v gpg &>/dev/null; then
                    sudo apt-get install -y gnupg
                fi

                # Add GPG key and repository
                sudo mkdir -p /usr/local/apt-keys
                gpg --batch --yes --fetch-keys \
                    https://neilalexander.s3.dualstack.eu-west-2.amazonaws.com/deb/key.txt
                gpg --batch --yes --export 1C5162E133015D81A811239D1840CDAC6011C5EA \
                    | sudo tee /usr/local/apt-keys/yggdrasil-keyring.gpg > /dev/null
                echo 'deb [signed-by=/usr/local/apt-keys/yggdrasil-keyring.gpg] https://neilalexander.s3.dualstack.eu-west-2.amazonaws.com/deb/ debian yggdrasil' \
                    | sudo tee /etc/apt/sources.list.d/yggdrasil.list > /dev/null

                sudo apt-get update -q
                sudo apt-get install -y yggdrasil

                # Generate config if it doesn't exist yet
                if [ ! -f /etc/yggdrasil/yggdrasil.conf ]; then
                    sudo yggdrasil -genconf \
                        | sudo tee /etc/yggdrasil/yggdrasil.conf >/dev/null

                    # Pre-populate with two working public peers
                    sudo python3 - <<'PYEOF'
import re
conf_path = '/etc/yggdrasil/yggdrasil.conf'
with open(conf_path) as f:
    conf = f.read()
peers = [
    'tls://london.sabretruth.org:18472',
    'tls://yggdrasil.neilalexander.dev:64648?key=ecbbcb3298e7d3b4196103333c3e839cfe47a6ca47602b94a6d596683f6bb358',
]
peer_lines = '\n'.join('  ' + p for p in peers)
conf = re.sub(r'Peers:\s*\[\s*\]', 'Peers: [\n' + peer_lines + '\n]', conf)
with open(conf_path, 'w') as f:
    f.write(conf)
PYEOF
                fi

                sudo systemctl enable yggdrasil
                sudo systemctl start yggdrasil

                YGG_ADDR=$(sudo yggdrasilctl getself 2>/dev/null \
                    | awk '/address/ {print $2}' || true)

                echo ""
                echo "  ✓ Yggdrasil installed and running."
                if [ -n "$YGG_ADDR" ]; then
                    echo "    Your address: $YGG_ADDR"
                fi
                echo ""
                echo "  Two public peers have been added to the Yggdrasil config"
                echo "  so it can connect to the network immediately."
                echo "  To change peers later, edit:"
                echo "    /etc/yggdrasil/yggdrasil.conf"
                echo ""
            fi
            ;;
        *)
            echo "  Skipping Yggdrasil — you can still connect to standard"
            echo "  Mumble servers using a hostname or IP address."
            echo ""
            ;;
    esac
fi

# ── Python ────────────────────────────────────────────────────────────────────
# pymumble v2 requires Python 3.12+

PYTHON=""
for candidate in python3.12 python3.13 python3.14 python3; do
    if command -v "$candidate" &>/dev/null; then
        PY_OK=$("$candidate" -c "import sys; print('ok' if sys.version_info >= (3,12) else '')" 2>/dev/null || true)
        if [ "$PY_OK" = "ok" ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    if command -v apt-get &>/dev/null; then
        echo "  pymumble v2 requires Python 3.12 or newer."
        echo "  Installing Python 3.12 via the deadsnakes PPA …"
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update -q
        sudo apt-get install -y python3.12 python3.12-venv python3.12-tk
        PYTHON="python3.12"
    else
        echo "ERROR: Python 3.12 or newer is required but not found."
        echo "       Please install Python 3.12 and re-run this script."
        exit 1
    fi
else
    PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if ! "$PYTHON" -c "import tkinter" 2>/dev/null && command -v apt-get &>/dev/null; then
        echo "  Installing python${PY_VER}-tk …"
        sudo apt-get install -y "python${PY_VER}-tk"
    fi
    if ! "$PYTHON" -c "import ensurepip" 2>/dev/null && command -v apt-get &>/dev/null; then
        echo "  Installing python${PY_VER}-venv …"
        sudo apt-get install -y "python${PY_VER}-venv"
    fi
fi

# ── Virtual environment ───────────────────────────────────────────────────────

if [ -f "$VENV/bin/python" ]; then
    echo "  ✓ Virtual environment already exists — skipping creation."
else
    if [ -d "$VENV" ]; then
        echo "  Removing incomplete virtual environment …"
        rm -rf "$VENV"
    fi
    echo "  Creating Python virtual environment …"
    "$PYTHON" -m venv "$VENV"
fi

# ── pymumble ──────────────────────────────────────────────────────────────────

echo "  Installing pymumble v2 …"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "git+https://codeberg.org/pymumble/pymumble.git"

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "┌─────────────────────────────────────┐"
echo "│          Setup complete!            │"
echo "└─────────────────────────────────────┘"
echo ""
echo "  Launch Mumble Chat:"
echo "    $SCRIPT_DIR/run_mumble_chat.sh"
echo ""
echo "  Or with arguments (skips the login dialog):"
echo "    $SCRIPT_DIR/run_mumble_chat.sh --host <address> --user <yourname>"
echo ""
