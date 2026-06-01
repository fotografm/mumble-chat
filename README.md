# Mumble Chat

A lightweight, text-only Mumble client with a clean dark GUI.  
No audio, no bloat — just chat, over an encrypted peer-to-peer network.

Built with Python and [pymumble v2](https://codeberg.org/pymumble/pymumble).

---

## Quick Start — single file, no setup required

This is the recommended way for most users.

**1. Download the latest release**

Go to the [Releases page](https://github.com/fotografm/mumble-chat/releases/latest) and download the file named:

```
mumble-chat-vX.Y.Z-linux.run
```

**2. Make it executable and run it**

```bash
chmod +x mumble-chat-vX.Y.Z-linux.run
./mumble-chat-vX.Y.Z-linux.run
```

That's it. The launcher will:
- Detect whether Yggdrasil is installed — if not, explain what it is and ask your permission to install it
- Configure Yggdrasil with two public peers so it can reach the network immediately
- Start Yggdrasil if it is not already running
- Open the Mumble Chat window
- Stop Yggdrasil when you close the app (only if the launcher started it — if Yggdrasil was already running it is left alone)

No Python install required. No FUSE or AppImage dependencies. Works on Ubuntu 22.04 and newer, Debian 11+, Linux Mint 21+.

> **Note:** The installer uses `sudo` only when needed (to install packages and manage the Yggdrasil service). You will be prompted for your password if required.

---

## Connecting

When the app opens, a login dialog appears. Fill in:

| Field | What to enter |
|---|---|
| **Host** | Yggdrasil address of the Mumble server (e.g. `201:abcd:...`) |
| **Port** | Server port — default is `64738` |
| **Username** | Your display name |
| **Password** | Server password, if required (leave blank if none) |
| **Channel** | Channel to join on connect (leave blank for root channel) |

Click **Connect**. The status bar at the top turns green when connected.

---

## Running from source (Python scripts)

Use this method if you want to run from the Git repository rather than the release binary — for development, or on machines where you prefer to manage the Python environment yourself.

### Requirements

- Ubuntu / Debian / Mint (the setup script uses `apt-get`)
- Python 3.12 or newer
- Internet access for the initial install

### First-time setup

```bash
git clone https://github.com/fotografm/mumble-chat.git
cd mumble-chat
bash setup_mumble_chat.sh
```

The setup script will:
1. Check if Yggdrasil is installed — offer to install it from the official repository if not
2. Configure Yggdrasil with two public peers (only on a fresh install)
3. Check for Python 3.12+ — install from the deadsnakes PPA if needed
4. Create a local Python virtual environment in `venv/`
5. Install `pymumble` into that environment

### Every time you want to run

```bash
bash run_mumble_chat.sh
```

The script starts Yggdrasil if it is not running, launches the app, and stops Yggdrasil again when you close the app.

### Command-line arguments

You can skip the login dialog by passing arguments directly:

```bash
bash run_mumble_chat.sh --host 201:xxxx:xxxx::1 --user Alice --channel General
```

| Argument | Description | Default |
|---|---|---|
| `--host` | Server address (Yggdrasil IPv6 or hostname) | *(dialog)* |
| `--port` | Server port | `64738` |
| `--user` | Your display name | *(dialog)* |
| `--password` | Server password | *(blank)* |
| `--channel` | Channel to join on connect | Root channel |

---

## NixOS

The setup script uses `apt-get` which does not exist on NixOS. Follow these steps instead.

### Yggdrasil on NixOS

Add Yggdrasil to your `configuration.nix`:

```nix
services.yggdrasil = {
  enable = true;
  settings = {
    Peers = [
      "tls://london.sabretruth.org:18472"
    ];
  };
};
```

Find additional peer addresses at **https://publicpeers.neilalexander.dev**, then apply:

```bash
sudo nixos-rebuild switch
```

Check your Yggdrasil address once the service is running:

```bash
sudo yggdrasilctl getself
```

### Python dependencies on NixOS

Even though Mumble Chat disables audio, `pymumble` imports `opuslib` at startup, and `opuslib` looks for `libopus.so` using the system library path. On NixOS, `libopus` lives in the Nix store and is not visible to the standard library search — this causes a crash on launch.

The fix is to enter a Nix shell that makes `libopus` and `tkinter` available before running the app. A `shell.nix` is included for this purpose.

### First-time setup on NixOS

```bash
git clone https://github.com/fotografm/mumble-chat.git
cd mumble-chat
nix-shell --run "bash setup_mumble_chat.sh"
```

The script will skip the Yggdrasil and `apt-get` steps automatically and set up only the Python virtual environment.

### Running on NixOS

```bash
cd mumble-chat
nix-shell --run "bash run_mumble_chat.sh"
```

Always launch via `nix-shell` so that `libopus` and `tkinter` are visible. Running `run_mumble_chat.sh` directly without `nix-shell` will fail with a library error.

---

## What is Yggdrasil?

[Yggdrasil](https://yggdrasil-network.github.io/) is a free, open-source, encrypted peer-to-peer overlay network. Think of it as a private internet that runs alongside the regular internet.

Every device that runs Yggdrasil gets a **permanent IPv6 address** in the `200::/7` range. This address is derived mathematically from a keypair generated on your machine — no registration, no central authority, no account required. If you reinstall Yggdrasil with the same key, you get the same address.

Yggdrasil devices can connect to each other through the network regardless of NAT, firewalls, or carrier-grade routers — as long as at least one device can reach a public peer node to relay traffic.

### Why use Yggdrasil with Mumble?

- **No port forwarding** — the server just runs; anyone on the Yggdrasil network reaches it via its address
- **Works through firewalls and NAT** — peer-to-peer routing finds a path through corporate networks and double-NAT
- **Stable, permanent addresses** — the address does not change when you move between networks or reboot
- **End-to-end encrypted** — relay nodes cannot read your traffic
- **No accounts or registration** — generate a keypair locally, connect to any public peer, you are on the network

### Finding your Yggdrasil address

Once Yggdrasil is running:

```bash
yggdrasilctl getself
```

The `address` field starts with `200:` or `203:`. Share this with anyone on the Yggdrasil network to let them reach services on your machine.

### Adding or changing peers

Edit the configuration file:

```bash
sudo nano /etc/yggdrasil/yggdrasil.conf
```

Find the `Peers:` section. A community list of public peers is at:

- **https://publicpeers.neilalexander.dev**
- https://github.com/yggdrasil-network/public-peers

After saving, restart Yggdrasil:

```bash
sudo systemctl restart yggdrasil
```

---

## Installing Yggdrasil manually

If you need to install Yggdrasil on a Debian/Ubuntu/Mint machine without running the setup script, use the official repository hosted by Neil Alexander:

```bash
sudo mkdir -p /usr/local/apt-keys
gpg --batch --yes --fetch-keys \
    https://neilalexander.s3.dualstack.eu-west-2.amazonaws.com/deb/key.txt
gpg --batch --yes --export 1C5162E133015D81A811239D1840CDAC6011C5EA \
    | sudo tee /usr/local/apt-keys/yggdrasil-keyring.gpg > /dev/null
echo 'deb [signed-by=/usr/local/apt-keys/yggdrasil-keyring.gpg] https://neilalexander.s3.dualstack.eu-west-2.amazonaws.com/deb/ debian yggdrasil' \
    | sudo tee /etc/apt/sources.list.d/yggdrasil.list
sudo apt update && sudo apt install -y yggdrasil
sudo yggdrasil -genconf | sudo tee /etc/yggdrasil/yggdrasil.conf > /dev/null
sudo systemctl enable --now yggdrasil
```

> **Note:** The old `deb.yggdrasil.io` domain no longer exists. Do not use it.

---

## Project layout

```
mumble-chat/
├── mumble_chat.py        Main application
├── setup_mumble_chat.sh  One-time installer (Debian/Ubuntu/Mint)
├── run_mumble_chat.sh    Launch script (source users)
├── shell.nix             Nix shell for NixOS users
├── venv/                 Python virtual environment (local, not in git)
└── README.md
```

---

## License

MIT
