# PRD — Relay

## 1. Vision du produit

Créer une application de messagerie en temps réel entièrement utilisable depuis un terminal, offrant une expérience proche de Claude Code. L'utilisateur n'a pas besoin d'ouvrir un navigateur : toute l'interface s'affiche directement dans le terminal.

Le produit doit être multiplateforme (Windows, Linux et macOS) et permettre à plusieurs utilisateurs de communiquer en temps réel via une interface TUI (Text User Interface).

---

# 2. Nom du projet

**Relay**

---

# 3. Objectif

Développer une application CLI moderne permettant :

* la communication instantanée entre utilisateurs ;
* la gestion de salons de discussion ;
* les conversations privées ;
* une interface élégante dans le terminal ;
* une faible consommation de ressources.

L'expérience utilisateur doit rappeler les outils modernes comme Claude Code, tout en étant dédiée à la messagerie.

---

# 4. Public cible

### Développeurs

Utilisateurs travaillant principalement dans le terminal.

### Administrateurs système

Communication rapide entre membres d'une équipe.

### Équipes techniques

Discussions liées aux projets sans quitter le terminal.

### Étudiants

Communication légère durant les travaux collaboratifs.

---

# 5. Objectifs fonctionnels

Le système doit permettre à un utilisateur de :

* créer un compte ;
* se connecter ;
* rejoindre plusieurs salons ;
* envoyer des messages en temps réel ;
* recevoir instantanément les messages des autres utilisateurs ;
* discuter en privé ;
* consulter son historique ;
* recevoir des notifications ;
* gérer son profil.

---

# 6. Fonctionnalités V1

## Authentification

* Inscription
* Connexion
* Déconnexion
* JWT
* Rafraîchissement automatique du token

---

## Profil

* Nom d'utilisateur
* Avatar (facultatif)
* Statut
* Dernière connexion

---

## Salons

* Créer un salon
* Rejoindre un salon
* Quitter un salon
* Liste des salons

---

## Messagerie

* Messages instantanés
* Historique
* Heure d'envoi
* Édition d'un message
* Suppression d'un message

---

## Messages privés

* Envoyer un DM
* Historique privé

---

## Présence

Afficher :

* En ligne
* Hors ligne
* Occupé
* Absent

---

## Notifications

Notification lorsqu'un utilisateur :

* vous écrit
* vous mentionne
* rejoint un salon

---

## Recherche

Recherche par :

* utilisateur
* salon
* message

---

# 7. Fonctionnalités V2

* Réactions 👍❤️🔥
* Réponses à un message
* Pièces jointes
* Images
* Vidéos
* Audio
* Emojis
* GIF
* Sondages

---

# 8. Fonctionnalités V3

* Appels audio
* Appels vidéo
* Partage d'écran
* IA intégrée
* Traduction automatique
* Plugins
* Bots

---

# 9. Interface

Disposition recommandée :

```text
┌──────────────────────────────────────────────────────────────┐
│ Relay                                ● Connecté     │
├───────────────┬──────────────────────────────────────────────┤
│ Salons        │ Général                                      │
│               │                                              │
│ # général     │ Amin : Salut                                │
│ # backend     │ John : Bonjour                              │
│ # devops      │ Hanif : Ça va ?                             │
│               │                                              │
├───────────────┴──────────────────────────────────────────────┤
│ >                                                          │
└──────────────────────────────────────────────────────────────┘
```

---

# 10. Raccourcis clavier

| Action        | Raccourci |
| ------------- | --------- |
| Nouveau salon | Ctrl + N  |
| Recherche     | Ctrl + K  |
| Quitter       | Ctrl + Q  |
| Historique    | Ctrl + H  |
| Effacer       | Ctrl + L  |

---

# 11. Commandes

```
/help

/login

/logout

/register

/profile

/channels

/join general

/leave

/users

/online

/dm amin

/history

/search django

/clear

/exit
```

---

# 12. Architecture

```
                  Relay
                         │
                   WebSocket (WSS)
                         │
               Django Channels Server
                         │
               ┌─────────┴──────────┐
               │                    │
             Redis            PostgreSQL
```

---

# 13. Stack technique

## Client

* Python 3.13+
* Textual
* Rich
* prompt_toolkit
* websockets
* httpx
* Typer

---

## Backend

* Django
* Django REST Framework
* Django Channels
* Redis
* PostgreSQL
* JWT

---

## Déploiement

* Docker
* Nginx
* Gunicorn
* Daphne
* HTTPS
* WebSocket sécurisé (WSS)

---

# 14. API

## Auth

```
POST /api/auth/register

POST /api/auth/login

POST /api/auth/refresh
```

---

## Utilisateurs

```
GET /api/users

GET /api/profile

PATCH /api/profile
```

---

## Salons

```
GET /api/channels

POST /api/channels

POST /api/channels/{id}/join

POST /api/channels/{id}/leave
```

---

## Messages

```
GET /api/messages

POST /api/messages
```

---

## WebSocket

```
wss://chat.example.com/ws/chat/
```

Événements :

* user_join
* user_leave
* message
* typing
* read
* edit
* delete
* notification

---

# 15. Base de données

## User

* id
* username
* email
* password
* avatar
* status
* created_at

---

## Channel

* id
* name
* description
* created_by

---

## Message

* id
* sender
* channel
* content
* edited
* created_at

---

## DirectMessage

* id
* sender
* receiver
* content
* created_at

---

# 16. Sécurité

* JWT
* WSS
* Hashage des mots de passe
* Protection contre le spam
* Limitation du débit (rate limiting)
* Validation des entrées
* Journalisation des événements

---

# 17. Performance

Objectifs :

* Connexion < 1 seconde
* Envoi d'un message < 100 ms sur un réseau stable
* Support initial : 5 000 utilisateurs connectés simultanément
* Reconnexion automatique après une perte de connexion

---

# 18. Roadmap

## Phase 1

* Authentification
* Interface Textual
* Salons
* Messagerie en temps réel
* Historique

---

## Phase 2

* Messages privés
* Notifications
* Présence
* Recherche
* Réactions

---

## Phase 3

* Partage de fichiers
* Plugins
* IA
* Chiffrement de bout en bout
* Synchronisation multi-appareils

---

# 19. Critères de réussite

* L'application fonctionne sur Windows, Linux et macOS.
* Les messages sont transmis en temps réel via WebSocket.
* L'interface reste fluide dans le terminal.
* Les utilisateurs peuvent rejoindre plusieurs salons et envoyer des messages sans quitter le terminal.
* La latence moyenne est inférieure à 100 ms dans des conditions réseau normales.
* L'architecture permet d'ajouter facilement de nouvelles fonctionnalités (bots, IA, plugins, partage de fichiers) sans refonte majeure.
