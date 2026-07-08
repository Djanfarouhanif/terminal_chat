"""Headless test of the REPL auth flow (staged + one-liner)."""
import asyncio
import os
import sys
import tempfile

os.environ["RELAY_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hanif_login_")
os.environ["RELAY_API"] = "http://127.0.0.1:8000"

from relay_cli.app import ChatApp  # noqa: E402
from textual.widgets import Input  # noqa: E402

SUF = str(os.getpid())
USER = f"login_{SUF}"


async def send(app, pilot, line, wait=0.5):
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
        check("Démarrage non authentifié", not app.session.is_authenticated)

        # Staged registration: /register with no args triggers field-by-field prompts.
        await send(app, pilot, "/register", wait=0.3)
        check("Flux d'inscription étagé démarré", app._auth_flow is not None)

        await send(app, pilot, USER, wait=0.2)           # username
        await send(app, pilot, f"{USER}@t.io", wait=0.2)  # email
        await send(app, pilot, "s3cretpwd!", wait=2.0)    # password -> submit

        check("Authentifié après inscription étagée", app.session.is_authenticated)
        check("Nom d'utilisateur mémorisé", app.session.username == USER)
        check("Flux d'auth terminé", app._auth_flow is None)

        # Logout then log back in with the one-liner form.
        await send(app, pilot, "/logout", wait=1.0)
        check("Déconnecté", not app.session.is_authenticated)

        await send(app, pilot, f"/login {USER} s3cretpwd!", wait=2.0)
        check("Reconnecté via one-liner /login", app.session.is_authenticated)

    print("\n" + "=" * 40)
    passed = sum(1 for _, c in results if c)
    print(f"RÉSULTAT: {passed}/{len(results)} tests réussis")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
