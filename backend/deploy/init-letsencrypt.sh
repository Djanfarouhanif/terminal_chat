#!/bin/sh
# ============================================================================
#  Bootstrap TLS Let's Encrypt pour Relay.
#  À lancer UNE fois sur le VPS, après avoir rempli .env.prod et pointé le DNS.
#  Usage : DOMAIN=chat.example.com EMAIL=vous@mail.com ./deploy/init-letsencrypt.sh
# ============================================================================
set -e

: "${DOMAIN:?Définissez DOMAIN=chat.example.com}"
: "${EMAIL:?Définissez EMAIL=vous@mail.com}"

COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "### 1/4 Certificat temporaire auto-signé (pour que Nginx démarre)…"
$COMPOSE run --rm --entrypoint "\
  sh -c 'mkdir -p $CERT_PATH && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout $CERT_PATH/privkey.pem \
    -out $CERT_PATH/fullchain.pem \
    -subj \"/CN=localhost\"'" certbot

echo "### 2/4 Démarrage de Nginx…"
$COMPOSE up -d nginx

echo "### 3/4 Suppression du certificat temporaire et demande du vrai…"
$COMPOSE run --rm --entrypoint "\
  sh -c 'rm -rf /etc/letsencrypt/live/$DOMAIN \
    /etc/letsencrypt/archive/$DOMAIN \
    /etc/letsencrypt/renewal/$DOMAIN.conf'" certbot

$COMPOSE run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email "$EMAIL" -d "$DOMAIN" \
  --rsa-key-size 4096 --agree-tos --no-eff-email --force-renewal

echo "### 4/4 Rechargement de Nginx avec le vrai certificat…"
$COMPOSE exec nginx nginx -s reload

echo "✅ TLS opérationnel pour https://$DOMAIN"
