"""Constantes de présentation (bannière, aide, thème) et petits utilitaires.

Ce module ne dépend ni de Textual ni de l'app : il est importable partout.
"""
from __future__ import annotations

BANNER = r"""[b green]
 ██████╗ ███████╗██╗      █████╗ ██╗   ██╗
 ██╔══██╗██╔════╝██║     ██╔══██╗╚██╗ ██╔╝
 ██████╔╝█████╗  ██║     ███████║ ╚████╔╝
 ██╔══██╗██╔══╝  ██║     ██╔══██║  ╚██╔╝
 ██║  ██║███████╗███████╗██║  ██║   ██║
 ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝[/]
[green]   R E L A Y   ::  [dim]secure terminal v0.1[/]
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


def escape(text) -> str:
    """Neutralise le balisage Rich dans du contenu utilisateur."""
    return str(text).replace("[", r"\[")


def version_tuple(v: str) -> tuple:
    out = []
    for part in str(v).split("."):
        digits = "".join(c for c in part if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)


def version_gt(latest: str, current: str) -> bool:
    """True si `latest` est strictement plus récent que `current`."""
    return version_tuple(latest) > version_tuple(current)
