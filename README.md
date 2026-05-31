# Mumble Chat

A lightweight, text-only Mumble client with a clean dark GUI.  
No audio, no bloat — just chat, over an encrypted peer-to-peer network.

Built with Python and [pymumble v2](https://codeberg.org/pymumble/pymumble).

---

## What is it?

Mumble Chat connects you to any [Mumble](https://www.mumble.info/) voice/chat server and lets you read and send channel messages in a simple desktop window. Audio is intentionally disabled — this is for text chat only, which makes it lightweight and suitable for low-power devices like a Raspberry Pi.

It is designed to work over **Yggdrasil**, an encrypted peer-to-peer IPv6 network, so you can reach Mumble servers anywhere in the world without worrying about firewalls, NAT, or port forwarding.

---

## Requirements

- Linux (Debian / Ubuntu / Mint recommended)
- Python 3.10 or newer
- Yggdrasil (strongly recommended — see below)
- Internet access for the initial install

---

## Installation

### 1. Download the files

No GitHub account is needed. First check that `git` is installed:

```bash
git --version
```

If you see `command not found`, install it first:

```bash
sudo apt install git
```

Then download Mumble Chat:

```bash
git clone https://github.com/fotografm/mumble-chat.git
cd mumble-chat
```

### 2. Run the setup script

```bash
bash setup_mumble_chat.sh
```

The script will:
- Check whether Yggdrasil is installed and offer to install it if not
- Pre-configure Yggdrasil with two public peers so it can connect immediately
- Install Python dependencies (`python3-tk`, `pymumble`)
- Create a local Python virtual environment inside the project folder

You will be asked for your password (`sudo`) only if packages need to be installed.

### 3. Launch

```bash
bash run_mumble_chat.sh
```

A login dialog will appear. Enter your Mumble server's address, port, your name, and (optionally) a channel name, then click **Connect**.

---

## NixOS

The standard setup script uses `apt-get` which does not exist on NixOS.
Follow these steps instead.

### Yggdrasil on NixOS

Yggdrasil is a system service on NixOS. Add it to your `configuration.nix`:

```nix
services.yggdrasil = {
  enable = true;
  settings = {
    Peers = [
      "tls://your-chosen-peer:port"
    ];
  };
};
```

Find peer addresses at **https://publicpeers.neilalexander.dev**, then rebuild:

```bash
sudo nixos-rebuild switch
```

Check your Yggdrasil address once the service is running:

```bash
sudo yggdrasilctl getself
```

### Python dependencies

Even though Mumble Chat disables audio, the `pymumble` library imports `opuslib`
at startup, and `opuslib` looks for `libopus.so` using the system library path.
On NixOS, `libopus` lives in the Nix store and is invisible to the standard
library search — this causes a crash on launch.

The fix is to enter a Nix shell that makes `libopus` and `tkinter` available
before setting up or running the app. A `shell.nix` is included in this
repository for exactly this purpose.

### Installing and running on NixOS

**First time only — set up the Python environment:**

```bash
git clone https://github.com/fotografm/mumble-chat.git
cd mumble-chat
nix-shell --run "bash setup_mumble_chat.sh"
```

The script will skip the Yggdrasil and `apt-get` steps automatically (since
those are not relevant on NixOS) and will create the Python virtual environment
with all required packages.

**Every time you want to run Mumble Chat:**

```bash
cd mumble-chat
nix-shell --run "bash run_mumble_chat.sh"
```

You must always launch via `nix-shell` so that `libopus` and `tkinter` are
visible to the application. Launching `run_mumble_chat.sh` directly without
`nix-shell` will fail with a library error.

---

## Running with command-line arguments

You can skip the login dialog by passing arguments directly:

```bash
bash run_mumble_chat.sh --host 200:xxxx:xxxx:xxxx::1 --user Alice --channel General
```

| Argument | Description | Default |
|---|---|---|
| `--host` | Server address (IPv6 or hostname) | *(dialog)* |
| `--port` | Server port | `64738` |
| `--user` | Your display name | *(dialog)* |
| `--password` | Server password | *(blank)* |
| `--channel` | Channel to join on connect | Root channel |

---

## What is Yggdrasil?

[Yggdrasil](https://yggdrasil-network.github.io/) is a free, open-source, encrypted peer-to-peer overlay network. Think of it as a private internet that runs alongside the regular internet.

Every device that runs Yggdrasil gets a **permanent IPv6 address** in the `200::/7` range. This address is derived mathematically from a keypair that is generated on your machine — no registration, no central authority, no account required. If you reinstall Yggdrasil with the same key, you get the same address.

Yggdrasil devices can connect directly to each other through the Yggdrasil network, regardless of whether they are behind NAT, a firewall, or a carrier-grade router — as long as at least one device can reach a public **peer** node to relay traffic.

---

## Advantages of using Yggdrasil with Mumble

### No port forwarding required
Running a standard Mumble server means opening a port on your router and keeping a fixed public IP or a dynamic DNS name. With Yggdrasil, the server just runs — anyone on the Yggdrasil network can reach it immediately using its Yggdrasil address.

### Works through firewalls and NAT
Corporate networks, mobile data connections, and double-NAT setups all block incoming connections. Yggdrasil's peer-to-peer routing finds a path through all of these, so both the server and the client can be behind restrictive firewalls.

### Stable, permanent addresses
Yggdrasil addresses do not change when you move between networks, change ISP, or reboot your router. Once you know a server's Yggdrasil address, it stays the same forever.

### End-to-end encrypted
All Yggdrasil traffic is encrypted between endpoints using modern cryptography. Even the relay nodes (peers) cannot read the content of your traffic.

### No accounts or registration
There is no sign-up process and no central service to go down. You generate a keypair locally, connect to any public peer, and you are immediately on the network.

### Great for community and mesh networks
Yggdrasil was designed for decentralised, community-run networks. It pairs naturally with ham radio mesh, off-grid communities, and privacy-conscious groups who want to run their own services without depending on commercial cloud infrastructure.

---

## Finding your Yggdrasil address

Once Yggdrasil is installed and running:

```bash
yggdrasilctl getself
```

Look for the `address` field — it will start with `200:` or `300:`.

You can share this address with anyone on the Yggdrasil network to let them connect to services running on your machine.

---

## Configuring Yggdrasil peers

After installation, Yggdrasil needs at least one **peer** to route traffic through. Edit the configuration file:

```bash
sudo nano /etc/yggdrasil/yggdrasil.conf
```

Find the `Peers:` section and add one or more public peer addresses. The best place to find peers is:

**https://publicpeers.neilalexander.dev**

A community-maintained backup list is also available at https://github.com/yggdrasil-network/public-peers

After saving, restart Yggdrasil:

```bash
sudo systemctl restart yggdrasil
```

---

## Project layout

```
mumble-chat/
├── mumble_chat.py        Main application
├── setup_mumble_chat.sh  One-time installer (Debian/Ubuntu/Mint)
├── run_mumble_chat.sh    Launch script
├── shell.nix             Nix shell for NixOS users
├── venv/                 Python environment (local, not committed to git)
└── README.md
```

---

## License

MIT
