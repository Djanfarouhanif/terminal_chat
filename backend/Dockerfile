# Image de production pour le backend Hanif Chat (ASGI / Daphne).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg[binary] embarque libpq : pas besoin de compiler.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# migrate + collectstatic sont exécutés au démarrage (la DB doit être prête).
RUN chmod +x deploy/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["deploy/entrypoint.sh"]
