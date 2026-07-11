# Lancer Relay en local (backend + client)

Ce guide explique comment démarrer le projet **Relay** sur ta machine, de zéro :
d'abord le **backend** (Django + WebSocket), puis le **client** (terminal).

> Ordre important : le **backend doit tourner avant** de lancer le client.

## Prérequis

- **Python 3.11+** (`python --version`)
- **Docker Desktop** (pour PostgreSQL + Redis)
- Un **vrai terminal** : sur Windows, **Windows Terminal** ou **PowerShell**
  (évite `cmd.exe` pour les couleurs et l'Unicode)
- **Git** (si tu clones le dépôt)

---

## 1. Backend — Django + Channels

### 1.1 Configuration

```powershell
cd backend
copy .env.example .env      # Windows PowerShell  (Linux/macOS : cp .env.example .env)
```

> Le port hôte de PostgreSQL est **5433** dans `.env` pour éviter un conflit
> avec un éventuel Postgres déjà installé sur 5432.

### 1.2 Lancer PostgreSQL + Redis

```powershell
docker compose up -d
```

Vérifie que les deux conteneurs tournent : `docker compose ps`
(tu dois voir `hanif-postgres` et `hanif-redis`).

### 1.3 Environnement Python + dépendances

```powershell
py -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt
```

> Linux / macOS :
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```

### 1.4 Migrations + démarrage

```powershell
./.venv/Scripts/python manage.py migrate
./.venv/Scripts/python manage.py runserver
```

Le serveur écoute sur **http://127.0.0.1:8000** (HTTP **et** WebSocket via Channels).

> Variante ASGI explicite (production-like) :
> ```powershell
> ./.venv/Scripts/python -m daphne -b 127.0.0.1 -p 8000 relay.asgi:application
> ```

### 1.5 (Optionnel) Vérifier que tout marche

```powershell
./.venv/Scripts/python e2e_test.py     # 14 vérifications REST + WebSocket
```

Laisse ce terminal **ouvert** : le backend doit rester actif.

---

## 2. Client — REPL terminal

Ouvre un **second terminal** (le backend continue de tourner dans le premier).

### 2.1 Environnement Python + dépendances

```powershell
cd client
py -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt
```

> Linux / macOS :
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```

### 2.2 Pointer le client vers le backend local

Par défaut le client vise la **prod**. Pour viser ton backend local, définis
l'URL de l'API :

```powershell
# Windows PowerShell
$env:RELAY_API = "http://127.0.0.1:8000"
./.venv/Scripts/python -m relay_cli
```

```bash
# Linux / macOS
RELAY_API=http://127.0.0.1:8000 python -m relay_cli
```

> Alternative persistante (enregistrée dans `~/.relay/config.json`) :
> ```powershell
> ./.venv/Scripts/python -m relay_cli chat --api http://127.0.0.1:8000
> ```

### 2.3 Premier usage

Dans le REPL :

```
/register monpseudo mon@email.fr monMotDePasse   # créer un compte
/login monpseudo monMotDePasse                   # ou se connecter
/join general                                    # rejoindre un salon
Salut tout le monde !                            # texte sans / = message envoyé
/help                                            # liste des commandes
/exit                                            # quitter
```

Les jetons JWT sont mémorisés dans `~/.relay/config.json` (auto-login ensuite).

---

## Récapitulatif express

| Étape | Terminal | Commande |
|------|----------|----------|
| 1 | Backend | `cd backend && copy .env.example .env` |
| 2 | Backend | `docker compose up -d` |
| 3 | Backend | `py -m venv .venv && ./.venv/Scripts/python -m pip install -r requirements.txt` |
| 4 | Backend | `./.venv/Scripts/python manage.py migrate` |
| 5 | Backend | `./.venv/Scripts/python manage.py runserver` |
| 6 | Client | `cd client && py -m venv .venv && ./.venv/Scripts/python -m pip install -r requirements.txt` |
| 7 | Client | `$env:RELAY_API="http://127.0.0.1:8000"; ./.venv/Scripts/python -m relay_cli` |

---

## Problèmes courants

- **Le client dit « AUTH REQUISE »** → normal au 1er lancement : fais `/register` ou `/login`.
- **Le client se connecte à la prod au lieu du local** → tu as oublié `RELAY_API` (§2.2).
- **`docker compose up` échoue** → Docker Desktop n'est pas démarré.
- **Port 5432/5433 déjà utilisé** → change `POSTGRES_PORT` dans `backend/.env`.
- **Couleurs/accents cassés sur Windows** → utilise Windows Terminal, pas `cmd.exe`.

---

## Pour aller plus loin

- API REST + WebSocket détaillées : [backend/README.md](backend/README.md)
- Commandes et raccourcis du client : [client/README.md](client/README.md)
- Installer le client sur une autre machine (pipx) : [client/INSTALL.md](client/INSTALL.md)
- Déploiement production : [backend/DEPLOY.md](backend/DEPLOY.md)
