# Relay — Client REPL (mode hacker)

Client terminal pour **Relay**. Interface **REPL mono-fenêtre** façon shell
hacker : vert phosphore sur noir, bannière ASCII, prompt `┌─user@relay:#salon`, tout
défile ligne par ligne. On tape des commandes ; les messages arrivent dans le flux.

## Stack
- Textual (RichLog défilant + prompt) + Rich
- httpx (REST) · websockets (temps réel)
- Typer (CLI)

## Installation & lancement

```bash
cd client
py -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # Linux/macOS

# Lancer (le backend doit tourner sur 127.0.0.1:8000)
./.venv/Scripts/python -m relay_cli
# backend distant :
./.venv/Scripts/python -m relay_cli chat --api https://chat.example.com
```

Après `pip install -e .`, la commande `relay` est disponible.

## Authentification

Au lancement, si aucune session n'est enregistrée, le REPL affiche `▸ AUTH REQUISE`.
Deux façons de s'authentifier :

```
/login                         → prompts étagés : username, puis password (masqué)
/login <user> <pass>           → one-liner
/register                      → prompts étagés : username, email, password
/register <user> <mail> <pass> → one-liner
```

Les jetons JWT sont stockés dans `~/.relay/config.json` (auto-login ensuite,
rafraîchissement automatique du token).

## Commandes

```
/help                     aide
/channels                 lister les salons
/create <nom>             créer un salon
/join <nom>               rejoindre / ouvrir un salon
/leave                    quitter le salon courant
/users   /online          lister les utilisateurs (● en ligne)
/dm <user> [msg]          message privé / historique
/history                  recharger l'historique du salon
/search <texte>           rechercher users + salons + messages
/edit <id> <texte>        éditer un de mes messages (temps réel)
/del <id>                 supprimer un de mes messages (temps réel)
/profile                  mon profil
/status <état>            online | busy | away | offline
/whoami                   infos de session
/clear                    effacer l'écran
/logout                   se déconnecter
/exit                     quitter
```

> Tapez du texte **sans `/`** pour l'envoyer au salon courant.
> Chaque message affiche son `#id` (utile pour `/edit` et `/del`).

## Raccourcis clavier

| Action        | Raccourci |
| ------------- | --------- |
| Nouveau salon | Ctrl + N  |
| Recherche     | Ctrl + K  |
| Effacer       | Ctrl + L  |
| Quitter       | Ctrl + Q  |

## Configuration

| Variable d'env     | Rôle                                             |
| ------------------ | ------------------------------------------------ |
| `RELAY_API`        | URL du backend (défaut `http://127.0.0.1:8000`)  |
| `RELAY_CONFIG_DIR` | Dossier de config/token (défaut `~/.relay`)      |

## Tests (headless, backend requis)

```bash
./.venv/Scripts/python tui_test.py     # 9 vérifs : auth, salon, WS temps réel, commandes
./.venv/Scripts/python login_test.py   # 7 vérifs : inscription étagée + login one-liner
./.venv/Scripts/python snapshot.py      # génère hacker_repl.svg (aperçu visuel)
```
