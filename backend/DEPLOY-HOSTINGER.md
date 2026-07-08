# Déploiement Relay — VPS Hostinger + Nginx système

Guide taillé pour **ton** serveur :
- VPS : `srv1153432.hstgr.cloud` (`82.112.240.14`)
- Domaine : `api-chat.hanifcode.fr` (DNS déjà pointé ✅)
- Nginx **déjà installé** sur le serveur → on l'utilise comme reverse-proxy.

Architecture : l'app tourne en Docker (web + postgres + redis) sur
`127.0.0.1:8000`, et le **Nginx du serveur** fait le TLS + proxy vers elle.

```
  Client CLI ─HTTPS/WSS─► Nginx système (TLS) ─► 127.0.0.1:8000 (Docker: Daphne)
                                                       │
                                              Redis + PostgreSQL (Docker)
```

---

## 1. Se connecter au VPS
```bash
ssh root@srv1153432.hstgr.cloud     # ou root@82.112.240.14
```

## 2. Installer Docker (si absent)
```bash
docker --version || curl -fsSL https://get.docker.com | sh
docker compose version
```

## 3. Récupérer le code
```bash
# Option git (recommandée) :
git clone <votre-repo> ~/relay && cd ~/relay/backend
# Option manuelle : envoyez le dossier backend/ via scp depuis votre PC :
#   scp -r backend root@srv1153432.hstgr.cloud:~/hanif-backend
```

## 4. Configurer l'environnement de prod
```bash
cp .env.prod.example .env.prod
nano .env.prod
```
Valeurs pour ton domaine :
```ini
SECRET_KEY=<colle ici : python3 -c "import secrets; print(secrets.token_urlsafe(64))">
DEBUG=False
ALLOWED_HOSTS=api-chat.hanifcode.fr
CSRF_TRUSTED_ORIGINS=https://api-chat.hanifcode.fr
POSTGRES_PASSWORD=<un mot de passe fort>
```

## 5. Lancer l'app en Docker
```bash
docker compose -f docker-compose.app.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.app.yml logs -f web   # doit finir par "Listening on TCP address 0.0.0.0:8000"
```
Test local sur le serveur :
```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: api-chat.hanifcode.fr" http://127.0.0.1:8000/api/channels
# 401 attendu = OK
```

## 6. Brancher le Nginx système
```bash
# copier le bloc serveur
cp deploy/nginx-host.conf /etc/nginx/sites-available/api-chat.hanifcode.fr
ln -sf /etc/nginx/sites-available/api-chat.hanifcode.fr /etc/nginx/sites-enabled/

# retirer la page par défaut « Welcome to nginx! » si elle occupe le port 80
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
```

## 7. Activer le HTTPS (Let's Encrypt via certbot système)
```bash
apt-get update && apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d api-chat.hanifcode.fr --agree-tos -m ton-email@exemple.com --redirect
```
Certbot modifie le bloc Nginx pour ajouter le TLS + la redirection HTTP→HTTPS,
et **renouvelle automatiquement** (timer systemd).

## 8. Vérifier depuis ta machine
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://api-chat.hanifcode.fr/api/channels   # 401
```
Puis le client :
```bash
# Windows PowerShell : $env:RELAY_API="https://api-chat.hanifcode.fr"; python -m relay_cli
RELAY_API=https://api-chat.hanifcode.fr python -m relay_cli
```
Le `https://` devient `wss://` automatiquement pour le temps réel.

## 9. Compte admin (optionnel)
```bash
docker compose -f docker-compose.app.yml exec web python manage.py createsuperuser
# admin sur https://api-chat.hanifcode.fr/admin/
```

---

## Exploitation

| Action | Commande (dans ~/relay/backend) |
|---|---|
| Logs | `docker compose -f docker-compose.app.yml logs -f web` |
| Redémarrer | `docker compose -f docker-compose.app.yml restart web` |
| Mettre à jour | `git pull && docker compose -f docker-compose.app.yml up -d --build web` |
| Sauvegarde DB | `docker compose -f docker-compose.app.yml exec postgres pg_dump -U hanif hanif > ~/backup-$(date +%F).sql` |
| Stopper | `docker compose -f docker-compose.app.yml down` |

## Pare-feu
N'exposez que **22** (SSH), **80** et **443**. Postgres/Redis ne sont **pas**
publiés hors du réseau Docker, et l'app n'écoute que sur `127.0.0.1` — bien.

## Sécurité
- Une fois HTTPS stable, mettez `SECURE_HSTS_SECONDS=31536000` dans `.env.prod`
  puis `docker compose -f docker-compose.app.yml up -d web`.
- `.env.prod` ne doit jamais être committé (déjà dans `.gitignore`).
