# ─── Stage 1 : build des dépendances ────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Copie uniquement le fichier de dépendances pour profiter du cache Docker
COPY app/requirements.txt .

# Installation dans un dossier isolé (pas dans le système)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2 : image finale légère ──────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Récupère uniquement les dépendances installées au stage 1
COPY --from=builder /install /usr/local

# Copie le code source de l'application
COPY app/app.py .

# Création d'un utilisateur non-root pour la sécurité
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser:appuser /app

USER appuser

# Port exposé par l'application
EXPOSE 5000

# Variables d'environnement par défaut (surchargées par K8s ConfigMap/Secret)
ENV AZURE_CONTAINER_NAME=content \
    CACHE_TTL=60 \
    PYTHONUNBUFFERED=1

# Lancement avec gunicorn (production-ready, pas flask run)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "30", "app:app"]