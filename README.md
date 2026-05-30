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

No GitHub account is needed. Run this command to download everything:

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
- Install Python dependencies (`python3-tk`, `pymumble`)
- Create a local Python virtual environment inside the project folder

You will be asked for your password (`sudo`) only if packages need to be installed.

### 3. Add a Yggdrasil peer

> **This step is required before Mumble Chat can connect to anything over Yggdrasil.**  
> Yggdrasil needs at least one public peer to route traffic through. Without one, your node is isolated.

Find a peer close to you at **https://publicpeers.neilalexander.dev** (or the community list at https://github.com/yggdrasil-network/public-peers). Copy one or more peer URIs — they look like `tls://hostname:port` or `tcp://hostname:port`.

Open the Yggdrasil config file:

```bash
sudo nano /etc/yggdrasil/yggdrasil.conf
```

Find the `Peers:` section and add your chosen peer(s):

```
Peers:
[
  tls://example-peer.net:12345
]
```

Save the file, then restart Yggdrasil:

```bash
sudo systemctl restart yggdrasil
```

Confirm you are connected:

```bash
yggdrasilctl getPeers
```

You should see at least one peer listed with a non-zero `uptime`.

### 4. Launch

```bash
bash run_mumble_chat.sh
```

A login dialog will appear. Enter your Mumble server's address, port, your name, and (optionally) a channel name, then click **Connect**.

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
├── setup_mumble_chat.sh  One-time installer
├── run_mumble_chat.sh    Launch script
├── venv/                 Python environment (local, not committed to git)
└── README.md
```

---

## License

MIT
