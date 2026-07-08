# Déploiement du site (platform Angular)

Le site est un build statique Angular servi par le Nginx du VPS, sur
**https://terminal-chat.hanifcode.fr**. Il consomme l'API du backend
(`https://api-chat.hanifcode.fr`) pour lister/servir les versions.

## Mettre à jour le site (après une modif du frontend)

```bash
# 1) Build de production (URL API prod injectée automatiquement)
cd platform
ng build

# 2) Transfert vers le VPS
cd dist/platform/browser
tar czf - . | ssh root@srv1153432.hstgr.cloud \
  "rm -rf /var/www/terminal-chat && mkdir -p /var/www/terminal-chat && tar xzf - -C /var/www/terminal-chat"
```
Rien d'autre à faire : Nginx sert les nouveaux fichiers immédiatement.

## Configuration serveur (déjà en place)

- **Nginx** : `/etc/nginx/sites-available/terminal-chat.hanifcode.fr`
  (racine `/var/www/terminal-chat`, fallback SPA `try_files … /index.html`).
- **TLS** : Let's Encrypt via `certbot --nginx` (renouvellement automatique).
- **DNS** : `terminal-chat.hanifcode.fr` → 82.112.240.14.

## Côté backend (source des versions)

- App `releases` : modèle `AppRelease` géré via l'**admin Django**
  (`https://api-chat.hanifcode.fr/admin/`).
- Endpoints publics : `GET /api/releases`, `/api/releases/latest`,
  `/api/releases/{id}/download`.
- Les installeurs uploadés sont stockés dans le **volume Docker `media`**
  (persistants aux redéploiements).
- `CORS_ALLOWED_ORIGINS` autorise `https://terminal-chat.hanifcode.fr`.

## Publier une nouvelle version (workflow admin)

1. Aller sur `https://api-chat.hanifcode.fr/admin/` → se connecter.
2. **Versions de l'application → Ajouter** : version, plateforme, notes,
   et **uploader l'installeur** (`Relay-Setup.exe`).
3. Enregistrer → la version apparaît aussitôt sur le site, téléchargeable.
4. (Option) mettre à jour `CLIENT_LATEST_VERSION` dans `.env.prod` pour
   déclencher l'avis de mise à jour dans le client déjà installé.
