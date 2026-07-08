"""Vérifie l'indicateur de connexion (badge auth) déconnecté puis connecté."""
import asyncio
import os
import sys
import tempfile

os.environ["RELAY_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hanif_conn_")
os.environ["RELAY_API"] = "http://127.0.0.1:8002"

from relay_cli.app import ChatApp  # noqa: E402
from textual.widgets import Input, Static  # noqa: E402

SUF = str(os.getpid())
USER = f"conn_{SUF}"


def ps1_top(app) -> str:
    return str(app.query_one("#ps1top", Static).render())


async def send(app, pilot, line, wait=0.4):
    app.query_one("#prompt", Input).value = line
    await pilot.press("enter")
    await asyncio.sleep(wait)
    await pilot.pause()


async def main() -> int:
    results = []

    def check(name, cond):
        results.append((name, cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {name}")

    app = ChatApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await asyncio.sleep(0.3)
        check("Badge 'déconnecté' visible au départ", "déconnecté" in ps1_top(app))

        await send(app, pilot, "/whoami", 0.3)
        check("/whoami dit 'déconnecté' hors connexion", "déconnecté" in "\n".join(app._transcript))

        await send(app, pilot, f"/register {USER} {USER}@t.io s3cretpwd!", 2.0)
        check("Authentifié", app.session.is_authenticated)
        check("Badge 'connecté' + pseudo après login", "connecté" in ps1_top(app) and USER in ps1_top(app))

        await send(app, pilot, f"/create room-{SUF}", 1.5)
        check("Badge 'live' après avoir rejoint un salon", "live" in ps1_top(app))

        await send(app, pilot, "/whoami", 0.4)
        joined = "\n".join(app._transcript)
        check("/whoami rapporte compte connecté + temps réel live",
              "compte    : connecté" in joined and "temps réel: live" in joined)

        await send(app, pilot, "/logout", 1.0)
        check("Badge repasse 'déconnecté' après /logout", "déconnecté" in ps1_top(app))

    passed = sum(1 for _, c in results if c)
    print(f"\nRÉSULTAT: {passed}/{len(results)} tests réussis")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
