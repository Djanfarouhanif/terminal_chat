"""Logique des commandes slash du REPL.

`CommandsMixin` est hérité par `ChatApp` : les méthodes utilisent donc les
attributs/méthodes définis sur l'app (self.api, self.session, self.socket,
self.sys/warn/err, self.load_channels, self.open_channel, self._do_auth…).
"""
from __future__ import annotations

from textual import work
from textual.widgets import RichLog

from .api import ApiError
from .ui import HELP_TEXT, escape


class CommandsMixin:
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

        # commandes autorisées sans authentification
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
