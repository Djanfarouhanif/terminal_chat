#!/bin/sh
set -e

echo "[entrypoint] Application des migrations…"
python manage.py migrate --noinput

echo "[entrypoint] Collecte des fichiers statiques…"
python manage.py collectstatic --noinput

echo "[entrypoint] Démarrage de Daphne (ASGI) sur :8000"
exec daphne -b 0.0.0.0 -p 8000 relay.asgi:application
