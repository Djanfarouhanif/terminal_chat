"""Typer entry point for the Hanif Chat CLI client."""
from __future__ import annotations

import typer

from . import __version__
from .app import ChatApp
from .config import CONFIG_FILE, Session

cli = typer.Typer(
    add_completion=False,
    help="Hanif Chat CLI — messagerie temps réel dans le terminal.",
)


@cli.command()
def chat(
    api: str = typer.Option(None, "--api", help="URL du backend (ex. http://127.0.0.1:8000)."),
):
    """Lancer l'interface de chat (commande par défaut)."""
    if api:
        session = Session.load()
        session.api_url = api
        session.save()
    ChatApp().run()


@cli.command()
def logout():
    """Effacer les identifiants enregistrés."""
    session = Session.load()
    session.clear()
    typer.echo("Déconnecté. Identifiants effacés.")


@cli.command()
def version():
    """Afficher la version."""
    typer.echo(f"Hanif Chat CLI {__version__}")


@cli.command()
def where():
    """Afficher l'emplacement du fichier de configuration."""
    typer.echo(str(CONFIG_FILE))


@cli.command()
def selftest():
    """Diagnostic : vérifie que l'interface démarre correctement."""
    import asyncio

    async def _go() -> bool:
        app = ChatApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
        return True

    try:
        ok = asyncio.run(_go())
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"FAIL: {exc}")
        raise typer.Exit(code=1)
    typer.echo("OK" if ok else "FAIL")


def main() -> None:
    # Bare invocation (no subcommand) launches the chat UI.
    import sys

    if len(sys.argv) == 1:
        ChatApp().run()
    else:
        cli()


if __name__ == "__main__":
    main()
