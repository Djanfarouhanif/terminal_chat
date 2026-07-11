# PRD (MVP) — Cyber Arena CLI

> **But de ce document** : définir le **plus petit jeu jouable et amusant** possible,
> pour prouver que 2 personnes prennent du plaisir avant de construire un jeu
> live-service complet. Tout ce qui n'est pas indispensable à cette preuve est
> **explicitement hors périmètre** (voir §10).

---

## 1. Positionnement

Cyber Arena CLI est un **jeu de duel compétitif** jouable depuis le terminal,
dans un univers de cybersécurité **entièrement fictif et simulé**.

**Repositionnement clé (vs le concept initial) :** on ne vise **pas** un jeu
temps réel nerveux façon PUBG/COD (impossible et frustrant dans un terminal).
On vise un **duel d'énigmes / d'intrusion, asynchrone et tour-par-tour**, dans
l'esprit d'un *chess.com du hacking fictif* : rapide, malin, rejouable, classé.

- **Asynchrone** : les 2 joueurs affrontent le **même défi** sans avoir à être
  en ligne en même temps → résout le problème du démarrage à froid.
- **Server-authoritative** : le serveur génère et valide tout ; le client ne
  fait qu'afficher et envoyer des actions → **anti-triche par conception**.

Lancement : `cyberarena`.

---

## 2. Objectif de l'MVP

Un joueur peut :
1. créer un compte et se connecter ;
2. lancer un **duel classé** (« Breach Duel ») contre un adversaire ;
3. résoudre une **intrusion simulée** générée par le serveur ;
4. voir son **score ELO** évoluer et sa position au **classement**.

**Critère de réussite unique :** *2 personnes jouent 3-4 duels d'affilée et ont
envie de recommencer.* Si non → on itère le mode, pas le reste.

---

## 3. Le mode de jeu : « Breach Duel » (1v1 asynchrone)

### Principe
Les deux joueurs reçoivent **exactement le même réseau fictif** (même seed).
Chacun le résout **seul et chronométré**. Le **meilleur score** gagne l'ELO.
On compare : objectif atteint ? puis **nombre d'actions**, puis **temps**.

### Le réseau (généré par le serveur, déterministe via seed)
Un petit graphe de **nœuds** (ex. 6 à 10). Chaque nœud a :
- un **type** (routeur, serveur, base de données, coffre…),
- un **verrou** = une **mini-énigme** à résoudre pour le « pirater ».

Objectif : atteindre le **nœud coffre** (`vault`) et l'**exfiltrer**.

### Les commandes du jeu (in-game, pas des commandes shell)
| Commande | Effet (validé serveur) |
|---|---|
| `scan` | Révèle les nœuds adjacents au nœud courant + le **type de verrou** de chacun |
| `move <node>` | Se déplacer vers un nœud **déjà déverrouillé** |
| `crack <node> <réponse>` | Tenter de résoudre le verrou du nœud (le serveur valide) |
| `hint <node>` | Indice (coûte des points / actions) |
| `exfiltrate` | Sur le `vault` déverrouillé → **fin de partie, victoire** |
| `status` | État : nœud courant, actions restantes, temps |

### Types de verrous (énigmes procédurales, 100 % serveur)
Pour l'MVP, **3 types** suffisent (contenu généré, pas écrit à la main) :
1. **Code** : deviner un nombre à 4 chiffres avec indices « plus/moins » (façon
   Mastermind allégé) — quelques tentatives.
2. **Motif** : compléter une suite logique (ex. `2 4 8 16 ?`).
3. **Déchiffrement** : petit César / substitution simple à retrouver.

Le serveur génère les énigmes depuis le **seed du duel** → les 2 joueurs ont
**strictement les mêmes**, donc l'affrontement est équitable.

### Score d'une manche
`score = base − (actions × cA) − (temps_s × cT) − (indices × cH)` (constantes à
régler). Objectif non atteint = score 0. Le serveur calcule et **stocke** le
score ; le client ne fait que jouer.

---

## 4. Boucle du joueur (MVP)

```
cyberarena
  └─ /login  (ou /register la 1re fois)
  └─ /duel            → matchmaking simple (file d'attente ELO)
        │  (adversaire trouvé — ou défi async repris plus tard)
        └─ résolution de l'intrusion (scan/crack/move/exfiltrate)
        └─ score enregistré → ELO mis à jour quand les 2 ont joué
  └─ /rank            → mon ELO, mon rang, mes dernières manches
  └─ /leaderboard     → top joueurs
  └─ /help  /quit
```

### Matchmaking MVP (volontairement simple)
- File d'attente : on associe 2 joueurs d'ELO proche.
- **S'il n'y a personne** : on propose un **défi asynchrone** — le joueur joue
  tout de suite le réseau ; son score attend qu'un adversaire prenne le même
  défi (ou un **bot** de niveau calibré, voir §10 « peut passer en MVP+ »).

---

## 5. ELO & classement
- **ELO** classique (K ajustable), mis à jour quand les **2 scores** d'un duel
  sont connus (gagnant = meilleur score).
- **Leaderboard** : top N par ELO (une seule ligue globale pour l'MVP).
- Historique : les X dernières manches du joueur (score, adversaire, résultat).

---

## 6. Architecture & stack (réutilise Relay)

```
   Client TUI (Textual)  ──WSS/HTTPS──►  Django + Channels
                                              │
                                     Redis (WS, files d'attente)
                                              │
                                        PostgreSQL
```

- **Client** : Python 3.13+, **Textual**, Rich, websockets, httpx, Typer.
- **Backend** : **Django** + **DRF** + **Django Channels** + **Redis** +
  **PostgreSQL** + **JWT**.
- **Déploiement** : réutilise **tout le pipeline Relay** (Docker, Nginx système,
  TLS, installeur Windows zippé, releases via l'admin, vérif de version).

> **Principe non négociable : server-authoritative.** Le client n'a **jamais**
> la solution ni le score. Il envoie des actions (`crack vault 1234`), le
> serveur valide et renvoie l'état. Toute la logique de jeu, la génération des
> énigmes et le calcul du score sont **côté serveur uniquement**.

---

## 7. Modèle de données (MVP)

- **Player** : id, username, email, password, elo (défaut 1000), created_at.
- **Match** : id, seed, status (`waiting` / `playing` / `finished`),
  created_at.
- **MatchEntry** : id, match, player, score (null tant que non joué),
  actions, time_ms, finished_at.
- **(dérivé)** classement = tri des Player par elo.

*Le réseau/énigmes ne sont pas stockés : ils sont **régénérés** depuis `seed`
à la volée côté serveur (déterministe).*

---

## 8. API & WebSocket (MVP)

**REST**
```
POST /api/auth/register        POST /api/auth/login        POST /api/auth/refresh
GET  /api/rank                 # mon elo, rang, historique
GET  /api/leaderboard          # top N
```

**WebSocket** `wss://…/ws/duel/`
- Client → serveur : `queue` (chercher un duel), puis actions de jeu
  (`scan`, `move`, `crack`, `hint`, `exfiltrate`, `status`).
- Serveur → client : `matched` (seed + état initial), `state` (après chaque
  action), `result` (score de la manche), `elo_update` (quand le duel se clôt).

---

## 9. Sécurité (héritée de Relay)
JWT, WSS, mots de passe hachés, rate-limiting, validation des entrées.
**Anti-triche = logique 100 % serveur** (le point le plus important).

---

## 10. Explicitement HORS périmètre MVP (à ne PAS construire)
> On y reviendra **seulement** si l'MVP est fun **et** a des joueurs.

- Clans / équipes, chat de guilde
- Saisons, ligues multiples, récompenses de saison
- Missions quotidiennes / défis hebdomadaires
- Cosmétiques / personnalisation de profil
- Coopératif, parties à +2 joueurs
- Matchmaking avancé (pools, files par région)
- Store, monnaie, progression XP/niveaux détaillée
- Modes de jeu supplémentaires

**Peut passer en « MVP+ » si besoin de contenu solo au lancement :**
- **Bots** d'entraînement calibrés (utile pour jouer même sans adversaire).

---

## 11. Jalons (proposés)
1. **Fondations** (réutilise Relay) : comptes + JWT + shell TUI + connexion WS.
2. **Moteur de jeu serveur** : génération réseau depuis seed + 3 types de
   verrous + validation des actions + calcul du score (avec tests).
3. **Duel de bout en bout** : file d'attente, une manche jouable au clavier,
   score enregistré.
4. **ELO + leaderboard** + historique.
5. **Playtest** : 2 joueurs, 3-4 duels → décision *fun / pas fun*.

---

## 12. Risques & garde-fous
- **Le fun** : risque n°1. Garde-fou → playtest dès le jalon 3, avant tout le reste.
- **Démarrage à froid** : mitigé par le mode **async** (+ bots en MVP+).
- **Triche** : mitigée par le **server-authoritative** dès le jour 1.
- **Scope creep** : la §10 est la ligne rouge. Rien de cette liste tant que le
  playtest n'est pas concluant.
