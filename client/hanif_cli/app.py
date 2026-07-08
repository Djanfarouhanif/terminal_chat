"""Hanif Chat CLI — REPL terminal (mode hacker).

Interface mono-fenêtre : un flux qui défile (RichLog) + un prompt façon shell.
Tout passe par des commandes tapées ; les messages arrivent dans le flux.
"""
from __future__ import annotations

from datetime import datetime

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, RichLog, Static

from .api import ApiClient, ApiError
from .config import Session

BANNER = r"""[b green]
 ██╗  ██╗ █████╗ ███╗   ██╗██╗███████╗
 ██║  ██║██╔══██╗████╗  ██║██║██╔════╝
 ███████║███████║██╔██╗ ██║██║█████╗
 ██╔══██║██╔══██║██║╚██╗██║██║██╔══╝
 ██║  ██║██║  ██║██║ ╚████║██║██║
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝[/]
[green]   H A N I F   C H A T   ::  [dim]secure terminal v0.1[/]
[dim green]   ─────────────────────────────────────────────[/]"""

HELP_TEXT = """[b green]COMMANDES DISPONIBLES[/]
  [green]/login[/] [dim][user] [pass][/]      s'authentifier
  [green]/register[/] [dim][u] [mail] [p][/]  créer un compte
  [green]/channels[/]                lister les salons
  [green]/create[/] [dim]<nom>[/]           créer un salon
  [green]/join[/] [dim]<nom>[/]             rejoindre / ouvrir un salon
  [green]/leave[/]                   quitter le salon courant
  [green]/users[/]  [green]/online[/]        lister les utilisateurs
  [green]/dm[/] [dim]<user> [msg][/]         message privé / historique
  [green]/history[/]                 recharger l'historique
  [green]/search[/] [dim]<texte>[/]         rechercher partout
  [green]/edit[/] [dim]<id> <texte>[/]      éditer un de mes messages
  [green]/del[/] [dim]<id>[/]              supprimer un de mes messages
  [green]/profile[/]  [green]/status <s>[/]   profil · statut online|busy|away|offline
  [green]/whoami[/]  [green]/clear[/]         infos session · effacer l'écran
  [green]/logout[/]  [green]/exit[/]          déconnexion · quitter
[dim]  Sans connexion : /login /register /help /clear /exit — le reste exige /login.
  Astuce : tapez du texte sans « / » pour l'envoyer au salon courant.[/]"""


class WSEvent(Message):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data


class WSStatus(Message):
    def __init__(self, status: str):
        super().__init__()
        self.status = status


HACKER_CSS = """
/* Mode hacker : vert phosphore sur noir, plein écran, style terminal. */
Screen { layout: vertical; background: #000000; color: #00ff5f; }
#log {
    height: 1fr; background: #000000; color: #00ff5f; padding: 0 1;
    scrollbar-background: #001a00; scrollbar-color: #00ff5f;
    scrollbar-size-vertical: 1;
}
#ps1top { height: 1; width: 1fr; background: #000000; color: #00ff5f; padding: 0 1; }
#promptline { height: 1; background: #000000; padding: 0 1; }
#ps1 { width: auto; height: 1; color: #00ff5f; background: #000000; }
#prompt {
    width: 1fr; height: 1; border: none; background: #000000;
    color: #00ff5f; padding: 0;
}
#prompt:focus { border: none; background: #000000; }
Input > .input--cursor { background: #00ff5f; color: #000000; }
Input > .input--placeholder { color: #005f2f; }
"""


class ChatApp(App):
    CSS = HACKER_CSS
    TITLE = "HANIF://SECURE_CHAT"

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
        self.current_channel: dict | None = None
        self._transcript: list[str] = []       # plain-text scrollback (tests/debug)
        self._auth_flow: dict | None = None     # staged login/register state

    # --- composition ---------------------------------------------------

    def compose(self) -> ComposeResult:
        yield RichLog(id="log", wrap=True, markup=True, highlight=False, auto_scroll=True)
        yield Static("", id="ps1top")
        with Horizontal(id="promptline"):
            yield Static("", id="ps1")
            yield Input(id="prompt")

    async def on_mount(self) -> None:
        self.print(BANNER)
        self.print(HELP_TEXT)          # commandes visibles dès le lancement, connecté ou non
        self._render_ps1()
        self.query_one("#prompt", Input).focus()
        if self.session.is_authenticated:
            self.println(f"[dim green]session restaurée : [/][green]{self.session.username}[/]")
            self.load_channels()
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
            f"[dim green]┌─[/] {auth} [dim green]@hanif :[/] "
            f"[green]#{escape(chan)}[/] [dim green]─[/] {link}"
        )
        inline.update("[dim green]└─$[/] ")

    # --- top-level input ----------------------------------------------

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

    # --- data loading --------------------------------------------------

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
            self.print(f"[dim green]  … {escape(e['username'])} écrit[/]")
        elif kind == "user_join":
            self.print(f"[dim green]  →→ {escape(e['username'])} a rejoint le canal[/]")
        elif kind == "user_leave":
            self.print(f"[dim green]  ←← {escape(e['username'])} a quitté le canal[/]")

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

    # --- commands ------------------------------------------------------

    @work(group="send")
    async def send_message(self, text: str) -> None:
        if self.socket is None or self.current_channel is None:
            self.warn("rejoignez un salon d'abord : /join <nom>")
            return
        await self.socket.send_message(text)

    @work(group="command")
    async def handle_command(self, text: str) -> None:
        parts = text[1:].split(" ")
        cmd = parts[0].lower()
        arg = " ".join(parts[1:]).strip()

        # commands allowed without auth
        if cmd == "login":
            bits = arg.split()
            if len(bits) >= 2:
                self._do_auth("login", {"username": bits[0], "password": " ".join(bits[1:])})
            else:
                self._start_auth("login")
            return
        if cmd == "register":
            bits = arg.split()
            if len(bits) >= 3:
                self._do_auth("register", {"username": bits[0], "email": bits[1], "password": " ".join(bits[2:])})
            else:
                self._start_auth("register")
            return
        if cmd == "help":
            self.print(HELP_TEXT)
            return
        if cmd in ("exit", "quit"):
            await self.action_quit()
            return
        if cmd == "clear":
            self.query_one("#log", RichLog).clear()
            self._transcript.clear()
            return
        if cmd == "whoami":
            self._report_connection()
            return

        if not self.session.is_authenticated:
            self.warn(f"/{cmd} exige une connexion. → /login <user> <pass>  ·  /help pour la liste")
            return

        try:
            if cmd == "channels":
                self.load_channels()
            elif cmd == "create":
                if not arg:
                    self.warn("usage : /create <nom>")
                    return
                ch = await self.api.create_channel(arg.replace(" ", "-"))
                self.sys(f"salon #{ch['name']} créé.")
                self.open_channel(ch)
            elif cmd == "join":
                if not arg:
                    self.warn("usage : /join <nom>")
                    return
                await self._join_by_name(arg)
            elif cmd == "leave":
                await self._leave_current()
            elif cmd in ("users", "online"):
                data = await self.api.users(online=(cmd == "online"))
                results = data["results"] if isinstance(data, dict) else data
                dot = {"online": "[green]●[/]", "busy": "[red]●[/]", "away": "[yellow]●[/]"}
                names = "  ".join(
                    f"{dot.get(u['status'], '[dim]○[/]')} {escape(u['username'])}" for u in results
                ) or "aucun"
                self.sys(f"utilisateurs : {names}")
            elif cmd == "dm":
                await self._handle_dm(arg)
            elif cmd == "history":
                await self._load_history()
            elif cmd == "search":
                await self._handle_search(arg)
            elif cmd == "edit":
                await self._handle_edit(arg)
            elif cmd in ("del", "delete"):
                await self._handle_delete(arg)
            elif cmd == "profile":
                p = await self.api.profile()
                self.sys(f"{p['username']} · {p['email']} · statut {p['status']}")
            elif cmd == "status":
                if arg not in ("online", "busy", "away", "offline"):
                    self.warn("usage : /status online|busy|away|offline")
                    return
                await self.api.update_profile(status=arg)
                self.sys(f"statut → {arg}")
            elif cmd == "logout":
                await self._logout()
            else:
                self.warn(f"commande inconnue : /{cmd}  (voir /help)")
        except ApiError as exc:
            self.err(f"erreur : {exc.detail}")
        except Exception as exc:  # noqa: BLE001
            self.err(f"erreur : {exc}")

    def _report_connection(self) -> None:
        """Afficher clairement l'état des deux connexions (compte + temps réel)."""
        if self.session.is_authenticated:
            self.print(f"[green]✓ compte    : connecté[/] [dim green]({escape(self.session.username)})[/]")
        else:
            self.print("[red]✗ compte    : déconnecté[/] [dim]— /login pour vous authentifier[/]")
        if self.socket is not None and self.current_channel:
            self.print(f"[green]✓ temps réel: live[/] [dim green](salon #{escape(self.current_channel['name'])})[/]")
        else:
            self.print("[dim green]○ temps réel: hors-salon[/] [dim]— /join <nom> pour recevoir en direct[/]")
        self.print(f"[dim green]· serveur    : {escape(self.session.api_url)}[/]")

    async def _join_by_name(self, name: str) -> None:
        data = await self.api.channels()
        results = data["results"] if isinstance(data, dict) else data
        target = next((c for c in results if c["name"] == name), None)
        if target is None:
            self.warn(f"salon introuvable : {name}  (créez-le : /create {name})")
            return
        self.open_channel(target)

    async def _leave_current(self) -> None:
        if not self.current_channel:
            self.warn("aucun salon courant.")
            return
        name = self.current_channel["name"]
        await self.api.leave_channel(self.current_channel["id"])
        if self.socket:
            await self.socket.close()
            self.socket = None
        self.current_channel = None
        self._render_ps1()
        self.sys(f"vous avez quitté #{name}.")

    async def _handle_dm(self, arg: str) -> None:
        if not arg:
            self.warn("usage : /dm <utilisateur> [message]")
            return
        bits = arg.split(" ", 1)
        user = bits[0]
        if len(bits) == 2 and bits[1].strip():
            await self.api.send_dm(user, bits[1].strip())
            self.sys(f"MP → {user} envoyé.")
        else:
            data = await self.api.dm_history(user)
            results = data["results"] if isinstance(data, dict) else data
            self.sys(f"— historique MP avec {user} —")
            for dm in results:
                self._print_message(f"dm{dm['id']}", dm["sender"], dm["content"], dm["created_at"], False)

    async def _handle_search(self, arg: str) -> None:
        if not arg:
            self.warn("usage : /search <texte>")
            return
        res = await self.api.search(arg)
        u = ", ".join(x["username"] for x in res["users"]) or "—"
        c = ", ".join("#" + x["name"] for x in res["channels"]) or "—"
        self.print(
            f"[b green]:: SEARCH « {escape(arg)} »[/]\n"
            f"  [green]users[/]    {escape(u)}\n"
            f"  [green]salons[/]   {escape(c)}\n"
            f"  [green]messages[/] {len(res['messages'])} trouvé(s)"
        )
        for m in res["messages"][:10]:
            self._print_message(m["id"], m["sender"], m["content"], m.get("created_at"), m.get("edited"))

    async def _handle_edit(self, arg: str) -> None:
        bits = arg.split(" ", 1)
        if len(bits) < 2 or not bits[0].isdigit():
            self.warn("usage : /edit <id> <nouveau texte>")
            return
        if self.socket is None:
            self.warn("rejoignez un salon d'abord.")
            return
        await self.socket.edit(int(bits[0]), bits[1].strip())

    async def _handle_delete(self, arg: str) -> None:
        if not arg.isdigit():
            self.warn("usage : /del <id>")
            return
        if self.socket is None:
            self.warn("rejoignez un salon d'abord.")
            return
        await self.socket.delete(int(arg))

    async def _logout(self) -> None:
        if self.socket:
            await self.socket.close()
            self.socket = None
        await self.api.logout()
        self.current_channel = None
        self._render_ps1()
        self.sys("déconnecté. /login pour revenir.")

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
        await self.api.aclose()


def escape(text) -> str:
    """Escape Rich markup in user-provided content."""
    return str(text).replace("[", r"\[")


def run() -> None:
    ChatApp().run()
