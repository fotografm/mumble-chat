#!/usr/bin/env python3
"""
mumble_chat.py — Text-only Mumble chat client (pymumble v2, Python 3.12+)
No audio. Connects to your Mumble server via Yggdrasil or any TCP route.

Install:
  pip install "git+https://codeberg.org/pymumble/pymumble.git"
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import traceback
import re
import sys
import argparse
import queue
from datetime import datetime

try:
    from mumble import Mumble
except ImportError:
    print("ERROR: mumble (pymumble v2) not found.")
    print("Install with:  pip install 'git+https://codeberg.org/pymumble/pymumble.git'")
    sys.exit(1)

VERSION = "1.0.10"

# ── Colour palette ─────────────────────────────────────────────────────────
BG        = "#0a0a18"
PANEL     = "#0f0f22"
BORDER    = "#3a3a7a"
BODY      = "#e8e8ff"
HEADING   = "#9999ff"
VALUE     = "#55ffaa"
MUTED     = "#9999cc"
ALERT     = "#ff6666"
SEND_BG   = "#1a1a3a"
INPUT_BG  = "#111128"
SELF_COL  = "#ffcc44"
SYS_COL   = "#55ffaa"
ERR_COL   = "#ff6666"
OTHER_COL = "#88ccff"
FONT_MONO = ("Courier New", 11)
FONT_UI   = ("Courier New", 10)
FONT_HEAD = ("Courier New", 13, "bold")


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)


class MumbleChatApp:
    def __init__(self, root, host, port, username, password, channel):
        self.root      = root
        self.host      = host
        self.port      = port
        self.username  = username
        self.password  = password
        self.channel   = channel
        self.mumble           = None
        self.connected        = False
        self.msg_queue        = queue.Queue()
        self._current_channel = None   # cached after join; fallback when myself is None
        # Event that fires once the connected callback (ServerSync) has run
        self._ready           = threading.Event()

        root.title("Mumble Chat  v%s" % VERSION)
        root.configure(bg=BG)
        root.geometry("1200x800")
        root.minsize(800, 600)

        self._build_ui()
        self._connect()
        self._poll_queue()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── Title bar
        title_frame = tk.Frame(root, bg=PANEL, pady=8)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="◈ MUMBLE CHAT  v%s" % VERSION, font=FONT_HEAD,
                 bg=PANEL, fg=HEADING).pack(side="left", padx=14)
        self.status_label = tk.Label(title_frame, text="● CONNECTING",
                                     font=FONT_UI, bg=PANEL, fg=ALERT)
        self.status_label.pack(side="right", padx=14)
        self.chan_label = tk.Label(title_frame, text="", font=FONT_UI,
                                   bg=PANEL, fg=MUTED)
        self.chan_label.pack(side="right", padx=6)

        tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

        # ── Main area: chat + users panel
        main = tk.Frame(root, bg=BG)
        main.pack(fill="both", expand=True)

        # Chat log (left, expands)
        chat_frame = tk.Frame(main, bg=BG)
        chat_frame.pack(side="left", fill="both", expand=True)
        self.chat_log = scrolledtext.ScrolledText(
            chat_frame, bg=BG, fg=BODY, font=FONT_MONO,
            insertbackground=VALUE, selectbackground=BORDER,
            selectforeground=BODY, relief="flat", bd=0,
            wrap="word", state="disabled", padx=12, pady=8)
        self.chat_log.pack(fill="both", expand=True)
        self.chat_log.tag_config("self",   foreground=SELF_COL)
        self.chat_log.tag_config("other",  foreground=OTHER_COL)
        self.chat_log.tag_config("system", foreground=SYS_COL)
        self.chat_log.tag_config("error",  foreground=ERR_COL)
        self.chat_log.tag_config("ts",     foreground=MUTED)

        # Users panel (right, fixed width)
        users_frame = tk.Frame(main, bg=PANEL, width=220)
        users_frame.pack(side="right", fill="y")
        users_frame.pack_propagate(False)
        tk.Label(users_frame, text="ONLINE", font=("Courier New", 9, "bold"),
                 bg=PANEL, fg=MUTED, pady=7).pack()
        tk.Frame(users_frame, bg=BORDER, height=1).pack(fill="x")
        self.users_list = tk.Listbox(
            users_frame, bg=PANEL, fg=VALUE, font=FONT_UI,
            relief="flat", bd=0, selectbackground=BORDER,
            selectforeground=BODY, activestyle="none", highlightthickness=0)
        self.users_list.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Separator before input
        tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

        # ── Input area — full height entry, not squashed
        input_frame = tk.Frame(root, bg=SEND_BG, pady=10)
        input_frame.pack(fill="x")

        self.nick_label = tk.Label(
            input_frame, text=self.username + " ▶",
            font=("Courier New", 11, "bold"), bg=SEND_BG, fg=SELF_COL)
        self.nick_label.pack(side="left", padx=(14, 6))

        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            input_frame, textvariable=self.input_var,
            bg=INPUT_BG, fg=BODY, insertbackground=VALUE,
            font=("Courier New", 12),
            relief="flat", bd=0,
            highlightthickness=2,
            highlightcolor=HEADING,
            highlightbackground=BORDER)
        self.input_box.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.input_box.bind("<Return>", self._send_message)
        self.input_box.bind("<Up>",     self._history_up)
        self.input_box.bind("<Down>",   self._history_down)

        send_btn = tk.Button(
            input_frame, text="SEND", command=self._send_message,
            bg=BORDER, fg=HEADING, font=("Courier New", 11, "bold"),
            relief="flat", padx=14, pady=6,
            activebackground=HEADING, activeforeground=BG, cursor="hand2")
        send_btn.pack(side="right", padx=(0, 14))

        self.msg_history = []
        self.history_pos = -1
        self.input_box.focus_set()

    # ── Connection ────────────────────────────────────────────────────────

    def _connect(self):
        self._sys_msg("Connecting to %s:%d ..." % (self.host, self.port))
        threading.Thread(target=self._mumble_thread, daemon=True).start()

    def _mumble_thread(self):
        """Runs in background thread. v2 uses context manager — blocks on __enter__."""
        try:
            m = Mumble(
                host=self.host,
                user=self.username,
                port=self.port,
                password=self.password,
                enable_audio=False,
                debug=False,
                reconnect=True,
            )
            self.mumble = m

            # Register callbacks BEFORE entering context manager
            m.callbacks.text_message_received.set_handler(self._on_text_message)
            m.callbacks.user_created.set_handler(self._on_user_join)
            m.callbacks.user_removed.set_handler(self._on_user_leave)
            m.callbacks.connected.set_handler(self._on_connected_cb)
            m.callbacks.disconnected.set_handler(self._on_disconnected_cb)

            # __enter__ starts the connection thread.  With reconnect=True it
            # returns after the FIRST attempt regardless of success, so we must
            # wait for the ServerSync-triggered connected callback before
            # proceeding — otherwise we call _post_connect on a dead socket.
            m.__enter__()
            if not self._ready.wait(timeout=60):
                self.msg_queue.put(("error",
                    "Server did not respond in 60 s. "
                    "Is Yggdrasil running and the address correct?"))
                self.msg_queue.put(("status", "disconnected"))
                return

            # Genuinely connected; do post-connect work:
            self._post_connect()

            # Now block keeping the connection alive until disconnected
            # Mumble IS the thread — join it directly
            m.join()

        except Exception as e:
            tb = traceback.format_exc()
            log_path = "/tmp/mumble-chat-error.log"
            try:
                with open(log_path, "w") as f:
                    f.write(tb)
            except Exception:
                pass
            self.msg_queue.put(("error",
                "Connection error: %s  (full traceback in %s)" % (e, log_path)))
            self.msg_queue.put(("status", "disconnected"))

    def _post_connect(self):
        # Wait for users.myself to be populated (up to 10s).
        # ServerSync fires before our own UserState on some server versions,
        # leaving myself=None until the UserState packet arrives separately.
        for _ in range(100):
            try:
                if self.mumble.users.myself is not None:
                    break
            except Exception:
                pass
            time.sleep(0.1)

        self.connected = True
        self.msg_queue.put(("status", "connected"))
        self.msg_queue.put(("system", "Connected as %s" % self.username))

        if self.channel:
            try:
                ch = self.mumble.channels.find_by_name(self.channel)
                ch.move_in()
                self._current_channel = ch
                self.msg_queue.put(("system", "Joined: %s" % self.channel))
                self.msg_queue.put(("chan", self.channel))
            except Exception as e:
                self.msg_queue.put(("error", "Channel error: %s" % e))
        else:
            try:
                ch = self.mumble.my_channel()
                self._current_channel = ch
                self.msg_queue.put(("chan", ch["name"]))
            except Exception:
                # my_channel() requires myself; fall back to root (channel 0)
                try:
                    ch = self.mumble.channels[0]
                    self._current_channel = ch
                    self.msg_queue.put(("chan", ch["name"]))
                except Exception:
                    pass

        self.msg_queue.put(("refresh_users",))

    def _on_connected_cb(self):
        self._ready.set()

    def _on_disconnected_cb(self):
        self.connected = False
        self.msg_queue.put(("status", "disconnected"))
        self.msg_queue.put(("error", "Disconnected from server."))

    def _on_text_message(self, message):
        try:
            actor_session = message.actor
            text = strip_html(message.message)
            actor_name = "?"
            try:
                actor_name = self.mumble.users[actor_session].name
            except Exception:
                pass
            kind = "self" if actor_name == self.username else "other"
            self.msg_queue.put((kind, actor_name, text))
        except Exception as e:
            self.msg_queue.put(("error", "Message error: %s" % e))

    def _on_user_join(self, user):
        try:
            name = user.name
        except Exception:
            name = "?"
        self.msg_queue.put(("system", "→ %s joined" % name))
        self.msg_queue.put(("refresh_users",))

    def _on_user_leave(self, user, event):
        try:
            name = user.name
        except Exception:
            name = "?"
        self.msg_queue.put(("system", "← %s left" % name))
        self.msg_queue.put(("refresh_users",))

    # ── Queue poller ──────────────────────────────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                kind = item[0]
                if kind == "status":
                    self._set_status(item[1])
                elif kind == "system":
                    self._append_line(item[1], "system")
                elif kind == "error":
                    self._append_line(item[1], "error")
                elif kind == "chan":
                    self.chan_label.config(text="[%s]" % item[1])
                elif kind in ("self", "other"):
                    _, name, text = item
                    ts = datetime.now().strftime("%H:%M")
                    self._append_chat(ts, name, text, kind)
                elif kind == "refresh_users":
                    self._update_users_list()
        except queue.Empty:
            pass
        self.root.after(80, self._poll_queue)

    def _set_status(self, status):
        if status == "connected":
            self.status_label.config(text="● CONNECTED", fg=VALUE)
        else:
            self.status_label.config(text="● OFFLINE", fg=ALERT)

    def _append_line(self, text, tag="system"):
        self.chat_log.config(state="normal")
        ts = datetime.now().strftime("%H:%M")
        self.chat_log.insert("end", "[%s] " % ts, "ts")
        self.chat_log.insert("end", text + "\n", tag)
        self.chat_log.config(state="disabled")
        self.chat_log.see("end")

    def _append_chat(self, ts, name, text, tag):
        self.chat_log.config(state="normal")
        self.chat_log.insert("end", "[%s] " % ts, "ts")
        self.chat_log.insert("end", "%s: " % name, tag)
        self.chat_log.insert("end", text + "\n", tag)
        self.chat_log.config(state="disabled")
        self.chat_log.see("end")

    def _sys_msg(self, text):
        self._append_line(text, "system")

    def _update_users_list(self):
        self.users_list.delete(0, "end")
        if self.mumble and self.connected:
            try:
                for user in self.mumble.users.by_name().values():
                    name = user.name
                    marker = "▶ " if name == self.username else "  "
                    self.users_list.insert("end", marker + name)
            except Exception:
                pass

    # ── Send ──────────────────────────────────────────────────────────────

    def _send_message(self, event=None):
        text = self.input_var.get().strip()
        if not text:
            return
        if not self.connected or self.mumble is None:
            self._append_line("Not connected.", "error")
            return
        try:
            # Prefer my_channel() (tracks moves); fall back to cached join target,
            # then root channel 0.  myself being None doesn't block sending.
            channel = None
            try:
                if self.mumble.users.myself is not None:
                    channel = self.mumble.my_channel()
            except Exception:
                pass
            if channel is None:
                channel = self._current_channel
            if channel is None:
                try:
                    channel = self.mumble.channels[0]
                except Exception:
                    pass
            if channel is None:
                self._append_line("Not in a channel yet — please wait.", "error")
                return
            channel.send_text_message(text)
            self.msg_history.insert(0, text)
            self.history_pos = -1
            self.input_var.set("")
            # Server never echoes your own messages back, so render locally
            ts = datetime.now().strftime("%H:%M")
            self._append_chat(ts, self.username, text, "self")
        except Exception as e:
            self._append_line("Send error: %s" % e, "error")

    def _history_up(self, event=None):
        if not self.msg_history:
            return
        self.history_pos = min(self.history_pos + 1, len(self.msg_history) - 1)
        self.input_var.set(self.msg_history[self.history_pos])
        self.input_box.icursor("end")

    def _history_down(self, event=None):
        if self.history_pos <= 0:
            self.history_pos = -1
            self.input_var.set("")
            return
        self.history_pos -= 1
        self.input_var.set(self.msg_history[self.history_pos])
        self.input_box.icursor("end")


# ── Connection dialog ────────────────────────────────────────────────────────

class ConnectDialog:
    def __init__(self, parent):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Connect to Mumble")
        self.top.configure(bg=BG)
        self.top.resizable(False, False)
        self.top.grab_set()

        # Centre on screen after widgets are laid out
        self.top.update_idletasks()
        sw = self.top.winfo_screenwidth()
        sh = self.top.winfo_screenheight()
        w  = self.top.winfo_reqwidth()
        h  = self.top.winfo_reqheight()
        self.top.geometry("+%d+%d" % ((sw - w) // 2, (sh - h) // 2))

        pad = {"padx": 14, "pady": 5}

        def row(label, default="", show=None):
            tk.Label(self.top, text=label, bg=BG, fg=HEADING,
                     font=FONT_UI, anchor="w").pack(fill="x", **pad)
            var = tk.StringVar(value=default)
            kw = dict(textvariable=var, bg=INPUT_BG, fg=BODY,
                      font=("Courier New", 12), relief="flat",
                      highlightthickness=2, highlightbackground=BORDER,
                      highlightcolor=HEADING, insertbackground=VALUE, bd=0)
            if show:
                kw["show"] = show
            tk.Entry(self.top, **kw).pack(fill="x", ipady=5, **pad)
            return var

        tk.Label(self.top, text="◈ MUMBLE CHAT — CONNECT",
                 font=FONT_HEAD, bg=BG, fg=HEADING, pady=14).pack()

        self.host_var = row("Server address  (IPv6 e.g. 200:xxxx:... or hostname)")
        self.port_var = row("Port", "64738")
        self.user_var = row("Your name / callsign")
        self.pass_var = row("Server password  (leave blank if none)", show="*")
        self.chan_var  = row("Channel name  (leave blank for root channel)")

        tk.Button(
            self.top, text="CONNECT", command=self._ok,
            bg=BORDER, fg=HEADING, font=("Courier New", 11, "bold"),
            relief="flat", padx=20, pady=8,
            activebackground=HEADING, activeforeground=BG,
            cursor="hand2").pack(pady=14)

        self.top.bind("<Return>", lambda e: self._ok())

    def _ok(self):
        host    = _sanitise_host(self.host_var.get())
        port    = int(self.port_var.get().strip() or "64738")
        user    = self.user_var.get().strip()
        passwd  = self.pass_var.get()
        channel = self.chan_var.get().strip() or None
        if not host or not user:
            messagebox.showerror("Missing fields",
                                 "Host and name are required.", parent=self.top)
            return
        self.result = (host, port, user, passwd, channel)
        self.top.destroy()


def _sanitise_host(host):
    """Strip an accidentally appended port from a host string.

    IPv6 hex groups contain a-f so they never match isdigit(). A trailing
    segment of pure digits (e.g. ':64738') is a misplaced port number.
    """
    host = host.strip()
    parts = host.rsplit(":", 1)
    if len(parts) == 2 and parts[1].isdigit():
        host = parts[0]
    return host


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Text-only Mumble chat client")
    parser.add_argument("--host",     default=None)
    parser.add_argument("--port",     default=64738, type=int)
    parser.add_argument("--user",     default=None)
    parser.add_argument("--password", default="")
    parser.add_argument("--channel",  default=None)
    args = parser.parse_args()

    root = tk.Tk()
    root.withdraw()          # hide blank window while the login dialog is open
    root.configure(bg=BG)

    host     = _sanitise_host(args.host) if args.host else None
    username = args.user
    port     = args.port
    password = args.password
    channel  = args.channel

    if not host or not username:
        dialog = ConnectDialog(root)
        root.wait_window(dialog.top)
        if not dialog.result:
            sys.exit(0)
        host, port, username, password, channel = dialog.result

    app = MumbleChatApp(root, host, port, username, password, channel)

    # Show the chat window and bring it to the front
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.focus_force()

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
