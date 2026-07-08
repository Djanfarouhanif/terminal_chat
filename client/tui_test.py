"""Headless smoke test for the Hanif REPL client (hacker mode).

Requires the backend running on 127.0.0.1:8000.
"""
import asyncio
import os
import sys
import tempfile

os.environ["HANIF_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hanif_test_")
os.environ["HANIF_API"] = "http://127.0.0.1:8000"

import httpx  # noqa: E402

from hanif_cli.app import ChatApp  # noqa: E402
from hanif_cli.config import Session  # noqa: E402
from textual.widgets import Input  # noqa: E402

SUF = str(os.getpid())
USER = {"username": f"tui_{SUF}", "email": f"tui_{SUF}@t.io", "password": "s3cretpwd!"}
CHAN = f"tui-room-{SUF}"


def pre_authenticate() -> None:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as c:
        c.post("/api/auth/register", json=USER)
        r = c.post("/api/auth/login", json={"username": USER["username"], "password": USER["password"]})
        r.raise_for_status()
        data = r.json()
    s = Session.load()
    s.access, s.refresh, s.username = data["access"], data["refresh"], data["user"]["username"]
    s.save()


async def run_cmd(app, pilot, line, wait=1.0):
    app.query_one("#prompt", Input).value = line
    await pilot.press("enter")
    await asyncio.sleep(wait)
    await pilot.pause()


async def main() -> int:
    pre_authenticate()
    results = []

    def check(name, cond):
        results.append((name, cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {name}")

    app = ChatApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await asyncio.sleep(1.0)
        check("Auto-login depuis token stocké", app.session.is_authenticated)

        t = lambda: "\n".join(app._transcript)

        await run_cmd(app, pilot, f"/create {CHAN}", wait=1.5)
        check("Salon courant après /create", app.current_channel and app.current_channel["name"] == CHAN)
        check("WebSocket connecté", app.socket is not None)

        await run_cmd(app, pilot, "Bonjour depuis le REPL", wait=1.5)
        check("Message affiché après round-trip WS", "Bonjour depuis le REPL" in t())

        await run_cmd(app, pilot, "/help", wait=0.4)
        check("/help affiche l'aide", "COMMANDES DISPONIBLES" in t())

        await run_cmd(app, pilot, "/users", wait=1.0)
        check("/users liste les utilisateurs", USER["username"] in t())

        await run_cmd(app, pilot, f"/search {CHAN}", wait=1.0)
        check("/search trouve le salon", "SEARCH" in t() and CHAN in t())

        await run_cmd(app, pilot, "/whoami", wait=0.4)
        check("/whoami affiche la session", USER["username"] in t())

        await run_cmd(app, pilot, "/clear", wait=0.3)
        check("/clear vide le transcript", len(app._transcript) == 0)

    print("\n" + "=" * 40)
    passed = sum(1 for _, c in results if c)
    print(f"RÉSULTAT: {passed}/{len(results)} tests réussis")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
