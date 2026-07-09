"""Relay — REPL terminal (mode hacker).

Interface mono-fenêtre : un flux qui défile (RichLog) + un prompt façon shell.
L'ossature (composition, rendu, WebSocket, prompt) est ici ; la logique des
commandes est dans `commands.py`, les constantes d'UI dans `ui.py`, les
messages internes dans `messages.py`.
"""
from __future__ import annotations

import time
from datetime import datetime

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, RichLog, Static

from .api import ApiClient, ApiError
from .commands import CommandsMixin
from .config import Session
from .messages import WSEvent, WSStatus
from .ui import BANNER, HACKER_CSS, HELP_TEXT, escape, version_gt


class ChatApp(CommandsMixin, App):
    CSS = HACKER_CSS
    TITLE = "RELAY://SECURE_CHAT"

    BINDINGS = [
        ("ctrl+q", "quit", "exit"),
        ("ctrl+l", "clear_view", "clear"),
        ("ctrl+k", "prefill_search", "search"),
        ("ctrl+n", "prefill_create", "new"),
    ]

    def __init__(self):
        super().__init__()
        self.session = Session.load()
        self.api = ApiClient(self.session)
        self.socket = None
        self.dm_socket = None                   # connexion perso pour les MP temps réel
        self.current_channel: dict | None = None
        self._transcript: list[str] = []       # plain-text scrollback (tests/debug)
        self._auth_flow: dict | None = None     # staged login/register state
        self._last_typing = 0.0                 # throttle des notifs « écrit »
        self._typers: dict[str, float] = {}     # qui écrit en ce moment (username -> t)

    # --- composition ---------------------------------------------------

    def compose(self) -> ComposeResult:
        yield RichLog(id="log", wrap=True, markup=True, highlight=False, auto_scroll=True)
        yield Static("", id="typing")
        yield Static("", id="ps1top")
        with Horizontal(id="promptline"):
            yield Static("", id="ps1")
            yield Input(id="prompt")

    async def on_mount(self) -> None:
        self.print(BANNER)
        # Aide complète seulement au tout premier lancement ; ensuite un rappel.
        if not self.session.help_shown:
            self.print(HELP_TEXT)
            self.session.help_shown = True
            self.session.save()
        else:
            self.print("[dim green]Tapez [/][green]/help[/][dim green] pour afficher les commandes.[/]")
        self._render_ps1()
        self.query_one("#prompt", Input).focus()
        self.set_interval(1.0, self._refresh_typing)  # expire l'indicateur « écrit »
        self.check_updates()
        if self.session.is_authenticated:
            self.println(f"[dim green]session restaurée : [/][green]{self.session.username}[/]")
            self.load_channels()
            self._connect_dm()
        else:
            self.println("[yellow]▸ AUTH REQUISE.[/] [dim]/login <user> <pass>  ·  /register <user> <email> <pass>[/]")

    # --- output helpers ------------------------------------------------

    def print(self, markup: str) -> None:
        self.query_one("#log", RichLog).write(markup)
        self._transcript.append(Text.from_markup(markup).plain)

    def println(self, markup: str) -> None:
        self.print(markup)

    def sys(self, text: str) -> None:
        self.print(f"[dim green]*[/] [green]{text}[/]")

    def err(self, text: str) -> None:
        self.print(f"[red]![/] [red]{escape(text)}[/]")

    def warn(self, text: str) -> None:
        self.print(f"[yellow]▸[/] [yellow]{escape(text)}[/]")

    # --- prompt (PS1) --------------------------------------------------

    def _render_ps1(self) -> None:
        prompt = self.query_one("#prompt", Input)
        top = self.query_one("#ps1top", Static)
        inline = self.query_one("#ps1", Static)
        if self._auth_flow:
            label, is_pass = self._auth_flow["fields"][self._auth_flow["idx"]]
            prompt.password = is_pass
            top.update("[dim green]┌─[ auth ][/]")
            inline.update(f"[dim green]└─[/][green]{label}[/][dim green]:[/] ")
            return
        prompt.password = False
        chan = self.current_channel["name"] if self.current_channel else "~"
        # Badge 1 : authentification (compte).
        if self.session.is_authenticated:
            auth = f"[green]✓ connecté[/] [dim green]{escape(self.session.username)}[/]"
        else:
            auth = "[red]✗ déconnecté[/] [dim red]anon[/]"
        # Badge 2 : lien temps réel (WebSocket sur un salon).
        link = "[green]● live[/]" if self.socket is not None else "[dim green]○ hors-salon[/]"
        top.update(
            f"[dim green]┌─[/] {auth} [dim green]@relay :[/] "
            f"[green]#{escape(chan)}[/] [dim green]─[/] {link}"
        )
        inline.update("[dim green]└─$[/] ")

    # --- top-level input ----------------------------------------------

    @on(Input.Changed, "#prompt")
    def _on_typing(self, event: Input.Changed) -> None:
        """Prévient les autres que je suis en train d'écrire (throttlé ~2 s)."""
        if self.socket is None or self.current_channel is None or self._auth_flow:
            return
        val = event.value
        if not val or val.startswith("/"):
            return
        now = time.monotonic()
        if now - self._last_typing < 2.0:
            return
        self._last_typing = now
        self._notify_typing()

    @work(group="typing")
    async def _notify_typing(self) -> None:
        if self.socket is not None:
            await self.socket.send_typing()

    @on(Input.Submitted, "#prompt")
    def _on_submit(self, event: Input.Submitted) -> None:
        raw = event.value
        self.query_one("#prompt", Input).value = ""
        if self._auth_flow is not None:
            self._feed_auth_flow(raw)
            return
        text = raw.strip()
        if not text:
            self._render_ps1()
            return
        # echo the command line, shell-style
        if text.startswith("/"):
            self.print(f"[dim green]└─$[/] [green]{escape(text)}[/]")
            self.handle_command(text)
        else:
            self.send_message(text)

    # --- staged auth flow ----------------------------------------------

    def _start_auth(self, mode: str) -> None:
        fields = (
            [("username", False), ("email", False), ("password", True)]
            if mode == "register"
            else [("username", False), ("password", True)]
        )
        self._auth_flow = {"mode": mode, "fields": fields, "idx": 0, "data": {}}
        self.sys(f"{mode.upper()} — renseignez les champs (Ctrl+Q pour annuler)")
        self._render_ps1()

    def _feed_auth_flow(self, value: str) -> None:
        flow = self._auth_flow
        field = flow["fields"][flow["idx"]][0]
        flow["data"][field] = value.strip() if field != "password" else value
        flow["idx"] += 1
        if flow["idx"] < len(flow["fields"]):
            self._render_ps1()
            return
        data = flow["data"]
        self._auth_flow = None
        self._render_ps1()
        self._do_auth(flow["mode"], data)

    @work(exclusive=True, group="auth")
    async def _do_auth(self, mode: str, data: dict) -> None:
        try:
            if mode == "register":
                if not (data.get("username") and data.get("email") and data.get("password")):
                    self.err("champs manquants pour l'inscription.")
                    return
                await self.api.register(data["username"], data["email"], data["password"])
                self.sys("compte créé.")
            if not (data.get("username") and data.get("password")):
                self.err("username et password requis.")
                return
            self.sys("authentification…")
            await self.api.login(data["username"], data["password"])
        except ApiError as exc:
            self.err(f"échec auth : {exc.detail}")
            return
        except Exception as exc:  # noqa: BLE001
            self.err(f"serveur injoignable : {exc}")
            return
        self.sys(f"connecté en tant que [b]{self.session.username}[/].")
        self._render_ps1()
        self.load_channels()
        self._connect_dm()

    # --- data loading --------------------------------------------------

    @work(group="update")
    async def check_updates(self) -> None:
        """Vérifie si une version plus récente du client est publiée."""
        from . import __version__

        try:
            data = await self.api.client_version()
        except Exception:  # noqa: BLE001 — check silencieux, jamais bloquant
            return
        latest = str(data.get("version", ""))
        url = data.get("download_url", "")
        if latest and version_gt(latest, __version__):
            self.warn(
                f"mise à jour disponible : v{latest} "
                f"(vous avez v{__version__}) → {url}"
            )

    @work(exclusive=True, group="channels")
    async def load_channels(self) -> None:
        try:
            data = await self.api.channels()
        except Exception as exc:  # noqa: BLE001
            self.err(f"chargement salons : {exc}")
            return
        results = data["results"] if isinstance(data, dict) else data
        if results:
            listing = "  ".join(f"[green]#{escape(c['name'])}[/]" for c in results)
            self.sys(f"{len(results)} salon(s) : {listing}")
        else:
            self.sys("aucun salon. Créez-en un : /create <nom>")

    @work(exclusive=True, group="open")
    async def open_channel(self, channel: dict) -> None:
        try:
            await self.api.join_channel(channel["id"])
        except ApiError:
            pass
        self.current_channel = channel
        self.print(f"[dim green]*** connexion à [/][green b]#{escape(channel['name'])}[/][dim green] ***[/]")
        await self._load_history()
        await self._connect_ws(channel["name"])
        self._typers.clear()
        self._refresh_typing()
        self._render_ps1()

    async def _load_history(self) -> None:
        if not self.current_channel:
            self.warn("aucun salon courant.")
            return
        try:
            data = await self.api.messages(self.current_channel["id"])
        except Exception as exc:  # noqa: BLE001
            self.err(f"historique : {exc}")
            return
        results = data["results"] if isinstance(data, dict) else data
        if not results:
            self.sys("— pas encore de messages —")
        for msg in results:
            self._print_message(
                msg["id"], msg["sender"], msg["content"], msg["created_at"], msg.get("edited")
            )

    async def _connect_ws(self, slug: str) -> None:
        if self.socket is not None:
            await self.socket.close()
        from .ws import ChatSocket

        self.socket = ChatSocket(
            self.session,
            slug,
            on_event=lambda e: self._dispatch_ws(e),
            on_status=lambda s: self.post_message(WSStatus(s)),
        )
        self.socket.start()

    async def _dispatch_ws(self, event: dict) -> None:
        self.post_message(WSEvent(event))

    def _connect_dm(self) -> None:
        """Ouvre la connexion perso pour recevoir les messages privés en direct."""
        if self.dm_socket is not None:
            return
        from .ws import DMSocket

        self.dm_socket = DMSocket(self.session, on_event=lambda e: self._dispatch_ws(e))
        self.dm_socket.start()

    # --- ws events -----------------------------------------------------

    @on(WSStatus)
    def _on_ws_status(self, message: WSStatus) -> None:
        if message.status == "reconnecting":
            self.warn("lien perdu — reconnexion…")
        elif message.status == "connected":
            self.sys("lien temps réel établi.")
        self._render_ps1()

    @on(WSEvent)
    def _on_ws_event(self, message: WSEvent) -> None:
        e = message.data
        kind = e.get("type")
        if kind == "message":
            self._print_message(e["id"], e["sender"], e["content"], e.get("created_at"), False)
        elif kind == "edit":
            self.print(f"[dim green]  ~ msg #{e['id']} édité ›[/] [green]{escape(e['content'])}[/]")
        elif kind == "delete":
            self.print(f"[dim green]  ~ msg #{e['id']} supprimé[/]")
        elif kind == "typing":
            self._typers[e["username"]] = time.monotonic()
            self._refresh_typing()
        elif kind == "user_join":
            self.print(f"[dim green]  →→ {escape(e['username'])} a rejoint le canal[/]")
        elif kind == "user_leave":
            self.print(f"[dim green]  ←← {escape(e['username'])} a quitté le canal[/]")
        elif kind == "dm_message":
            sender = e.get("sender", "?")
            content = e.get("content", "")
            if sender == self.session.username:
                # écho de mon propre MP envoyé
                self.print(f"[magenta]✉ → {escape(e.get('receiver', '?'))}[/][dim green]>[/] {escape(content)}")
            else:
                self.bell()  # notification sonore
                self.print(f"[magenta b]✉ {escape(sender)}[/][dim] (privé)[/][dim green]>[/] {escape(content)}")

    def _refresh_typing(self) -> None:
        """Affiche « … x écrit » sur une ligne dédiée et retire ceux qui ont arrêté."""
        now = time.monotonic()
        self._typers = {u: t for u, t in self._typers.items() if now - t < 3.5}
        names = list(self._typers.keys())
        if not names:
            text = ""
        elif len(names) == 1:
            text = f"… {escape(names[0])} écrit…"
        elif len(names) == 2:
            text = f"… {escape(names[0])}, {escape(names[1])} écrivent…"
        else:
            text = f"… {escape(names[0])}, {escape(names[1])} +{len(names) - 2} écrivent…"
        try:
            self.query_one("#typing", Static).update(text)
        except Exception:  # noqa: BLE001 — widget absent pendant le teardown
            pass

    # --- message rendering ---------------------------------------------

    def _fmt_time(self, iso: str | None) -> str:
        if not iso:
            return datetime.now().strftime("%H:%M:%S")
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%H:%M:%S")
        except ValueError:
            return "??:??:??"

    def _print_message(self, msg_id, sender, content, created_at, edited) -> None:
        mine = sender == self.session.username
        who = "bright_green" if mine else "green"
        tag = f" [dim green]#{msg_id}[/]"
        edited_tag = " [dim](édité)[/]" if edited else ""
        self.print(
            f"[dim green]{self._fmt_time(created_at)}[/]{tag} "
            f"[{who} b]{escape(sender)}[/][dim green]>[/] {escape(content)}{edited_tag}"
        )

    # --- key actions ---------------------------------------------------

    def action_clear_view(self) -> None:
        self.query_one("#log", RichLog).clear()
        self._transcript.clear()

    def action_prefill_search(self) -> None:
        self._prefill("/search ")

    def action_prefill_create(self) -> None:
        self._prefill("/create ")

    def _prefill(self, text: str) -> None:
        prompt = self.query_one("#prompt", Input)
        prompt.value = text
        prompt.cursor_position = len(text)
        prompt.focus()

    async def on_unmount(self) -> None:
        if self.socket:
            await self.socket.close()
        if self.dm_socket:
            await self.dm_socket.close()
        await self.api.aclose()


def run() -> None:
    ChatApp().run()
