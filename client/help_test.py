"""Vérifie que la liste des commandes s'affiche au démarrage SANS connexion."""
import asyncio
import os
import sys
import tempfile

os.environ["HANIF_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hanif_help_")
os.environ["HANIF_API"] = "http://127.0.0.1:8002"

from hanif_cli.app import ChatApp  # noqa: E402
from textual.widgets import Input  # noqa: E402


async def main() -> int:
    results = []

    def check(name, cond):
        results.append((name, cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {name}")

    app = ChatApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await asyncio.sleep(0.3)
        t = "\n".join(app._transcript)
        check("Non authentifié au démarrage", not app.session.is_authenticated)
        check("Liste des commandes affichée au lancement", "COMMANDES DISPONIBLES" in t)
        check("Aide mentionne les commandes hors connexion", "Sans connexion" in t)

        # /help redemandé hors connexion fonctionne toujours
        app.query_one("#prompt", Input).value = "/help"
        await pilot.press("enter")
        await asyncio.sleep(0.3)
        await pilot.pause()
        check("/help fonctionne hors connexion", "\n".join(app._transcript).count("COMMANDES DISPONIBLES") >= 2)

        # une commande protégée renvoie un message utile
        app.query_one("#prompt", Input).value = "/channels"
        await pilot.press("enter")
        await asyncio.sleep(0.3)
        await pilot.pause()
        check("Commande protégée guide vers /login", "exige une connexion" in "\n".join(app._transcript))

    passed = sum(1 for _, c in results if c)
    print(f"\nRÉSULTAT: {passed}/{len(results)} tests réussis")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
