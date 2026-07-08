# Déploiement Production — Relay (VPS · Docker · Nginx · TLS)

Guide pas à pas pour héberger le backend sur un serveur Linux, accessible en
HTTPS/WSS. Le client (`../client`) est ensuite distribué aux utilisateurs, qui
le pointent vers votre domaine.

## Architecture déployée

```
  Client CLI  ──HTTPS/WSS──►  Nginx (TLS)  ──►  Daphne (ASGI, Django Channels)
                                                     │
                                            ┌────────┴────────┐
                                         Redis            PostgreSQL
```

Fichiers concernés : `Dockerfile`, `docker-compose.prod.yml`,
`deploy/nginx.conf`, `deploy/entrypoint.sh`, `deploy/init-letsencrypt.sh`,
`.env.prod`.

---

## Prérequis

1. Un **VPS** Linux (Ubuntu/Debian) avec **Docker** + **plugin compose**.
2. Un **nom de domaine** dont l'enregistrement **DNS A** pointe vers l'IP du VPS
   (ex. `chat.example.com → 203.0.113.10`).
3. Les ports **80** et **443** ouverts dans le pare-feu.

---

## Étapes

### 1. Récupérer le code sur le VPS
```bash
git clone <votre-repo> relay && cd relay/backend
# (ou copiez le dossier backend/ via scp/rsync)
```

### 2. Configurer l'environnement
```bash
cp .env.prod.example .env.prod
nano .env.prod        # SECRET_KEY, mots de passe, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
```
Générer une `SECRET_KEY` :
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Mettre votre domaine dans la conf Nginx
```bash
sed -i 's/chat.example.com/VOTRE.DOMAINE/g' deploy/nginx.conf
```

### 4. Construire et lancer l'application (sans TLS encore)
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build web postgres redis
```
`web` applique les migrations et le collectstatic automatiquement au démarrage
(voir `deploy/entrypoint.sh`). Vérifiez :
```bash
docker compose -f docker-compose.prod.yml logs -f web
```

### 5. Obtenir le certificat TLS (Let's Encrypt)
```bash
chmod +x deploy/init-letsencrypt.sh
DOMAIN=VOTRE.DOMAINE EMAIL=vous@mail.com ./deploy/init-letsencrypt.sh
```
Le script crée un certificat temporaire, démarre Nginx, obtient le vrai
certificat par challenge HTTP, puis recharge Nginx. Le service `certbot` le
**renouvelle automatiquement** ensuite (toutes les 12 h).

### 6. Tout démarrer
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 7. Créer un compte admin (optionnel, pour /admin)
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Vérifier

```bash
# REST (401 attendu sans token = OK)
curl -s -o /dev/null -w "%{http_code}\n" https://VOTRE.DOMAINE/api/channels
```
Puis, côté client :
```bash
RELAY_API=https://VOTRE.DOMAINE python -m relay_cli
# ou : python -m relay_cli chat --api https://VOTRE.DOMAINE
```
Le schéma `https://` est automatiquement converti en `wss://` pour le temps réel.

---

## Exploitation

| Action | Commande |
|---|---|
| Logs | `docker compose -f docker-compose.prod.yml logs -f web nginx` |
| Redémarrer | `docker compose -f docker-compose.prod.yml restart web` |
| Mettre à jour | `git pull && docker compose -f docker-compose.prod.yml up -d --build web` |
| Sauvegarde DB | `docker compose -f docker-compose.prod.yml exec postgres pg_dump -U hanif hanif > backup.sql` |
| Arrêter | `docker compose -f docker-compose.prod.yml down` |

---

## Sécurité — checklist avant ouverture au public

- [ ] `DEBUG=False` et `SECRET_KEY` unique/secrète dans `.env.prod`.
- [ ] `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` limités à votre domaine.
- [ ] Mots de passe Postgres forts ; `.env.prod` **non committé**.
- [ ] Une fois HTTPS stable, mettez `SECURE_HSTS_SECONDS=31536000`.
- [ ] Pare-feu : n'exposez que 80/443 (22 pour SSH). Postgres/Redis restent
      internes au réseau Docker (aucun `ports:` publié pour eux).
- [ ] Sauvegardes régulières du volume `pgdata`.
