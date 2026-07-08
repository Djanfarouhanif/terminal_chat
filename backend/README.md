# Relay — Backend

Backend temps réel (Django + DRF + Channels) pour la messagerie terminal **Relay**.

## Stack
- Django 5 + Django REST Framework
- Django Channels (WebSocket) + Redis
- PostgreSQL
- JWT (SimpleJWT)

## Démarrage rapide

```bash
cd backend
cp .env.example .env                     # config par défaut (Postgres sur 5433)
docker compose up -d                     # PostgreSQL + Redis

py -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # Linux/macOS

python manage.py migrate
python manage.py runserver               # dev HTTP+WS via runserver (Channels)
# ou en ASGI explicite :
python -m daphne -b 127.0.0.1 -p 8000 relay.asgi:application
```

> Le port hôte de PostgreSQL est **5433** (`POSTGRES_PORT` dans `.env`) pour éviter
> un conflit avec une éventuelle installation locale de Postgres sur 5432.

## API REST

| Méthode | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Inscription |
| POST | `/api/auth/login` | Connexion → `access` + `refresh` + `user` |
| POST | `/api/auth/refresh` | Rafraîchir le token |
| POST | `/api/auth/logout` | Déconnexion (passe hors ligne) |
| GET/PATCH | `/api/profile` | Profil de l'utilisateur courant |
| GET | `/api/users?online=1&search=` | Liste des utilisateurs |
| GET/POST | `/api/channels` | Lister / créer un salon |
| POST | `/api/channels/{id}/join` | Rejoindre |
| POST | `/api/channels/{id}/leave` | Quitter |
| GET/POST | `/api/messages?channel={id}` | Historique / envoyer |
| GET/PATCH/DELETE | `/api/messages/{id}` | Éditer / supprimer (auteur seulement) |
| GET/POST | `/api/dm?user={username}` | Messages privés |
| GET | `/api/search?q=` | Recherche users + salons + messages |

Toutes les routes (sauf register/login/refresh) nécessitent l'en-tête
`Authorization: Bearer <access>`.

## WebSocket

```
ws://127.0.0.1:8000/ws/chat/<slug-du-salon>/?token=<access>
```

Événements client → serveur : `message`, `typing`, `edit`, `delete`.
Événements serveur → client : `message`, `typing`, `edit`, `delete`, `user_join`, `user_leave`.

Exemple d'envoi : `{"type": "message", "content": "Salut"}`

## Test bout en bout

```bash
python -m pip install httpx websockets
python e2e_test.py     # 14 vérifications REST + WebSocket
```
