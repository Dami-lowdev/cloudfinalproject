import os
import json
import logging
from datetime import datetime

import yaml
from flask import Flask, jsonify, render_template_string
from azure.storage.blob import BlobServiceClient
from cachetools import TTLCache, cached

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

AZURE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
CONTAINER_NAME = os.environ.get("AZURE_CONTAINER_NAME", "content")
CACHE_TTL = int(os.environ.get("CACHE_TTL", "60"))

# Cache mémoire : max 10 entrées, TTL configurable (défaut 60s)
cache = TTLCache(maxsize=10, ttl=CACHE_TTL)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_blob_client():
    """Retourne un BlobServiceClient à partir de la connection string."""
    if not AZURE_CONNECTION_STRING:
        raise EnvironmentError("AZURE_STORAGE_CONNECTION_STRING non définie")
    return BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)


def read_blob(filename: str) -> dict:
    """
    Lit un fichier JSON ou YAML depuis Azure Blob Storage.
    Résultat mis en cache via TTLCache.
    """
    if filename in cache:
        logger.info("Cache HIT pour %s", filename)
        return cache[filename]

    logger.info("Cache MISS — lecture Blob : %s", filename)
    client = get_blob_client()
    blob = client.get_blob_client(container=CONTAINER_NAME, blob=filename)
    raw = blob.download_blob().readall().decode("utf-8")

    if filename.endswith(".yaml") or filename.endswith(".yml"):
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)

    cache[filename] = data
    return data


def make_error(message: str, status: int = 500):
    logger.error(message)
    return jsonify({"error": message}), status


# ---------------------------------------------------------------------------
# Endpoints API
# ---------------------------------------------------------------------------

@app.route("/api/events", methods=["GET"])
def get_events():
    try:
        data = read_blob("events.json")
        return jsonify({"items": data.get("items", data)}), 200
    except Exception as e:
        return make_error(f"Impossible de lire events.json : {e}")


@app.route("/api/news", methods=["GET"])
def get_news():
    try:
        data = read_blob("news.json")
        return jsonify({"items": data.get("items", data)}), 200
    except Exception as e:
        return make_error(f"Impossible de lire news.json : {e}")


@app.route("/api/faq", methods=["GET"])
def get_faq():
    try:
        data = read_blob("faq.json")
        return jsonify({"items": data.get("items", data)}), 200
    except Exception as e:
        return make_error(f"Impossible de lire faq.json : {e}")


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

@app.route("/healthz", methods=["GET"])
def healthz():
    """Liveness probe — l'app tourne-t-elle ?"""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route("/readyz", methods=["GET"])
def readyz():
    """Readiness probe — l'app est-elle prête à recevoir du trafic ?"""
    if not AZURE_CONNECTION_STRING:
        return jsonify({"status": "not ready", "reason": "AZURE_STORAGE_CONNECTION_STRING manquante"}), 503
    return jsonify({"status": "ready", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route("/api/version", methods=["GET"])
def get_version():
    """Retourne la version et les metadonnees de l'application."""
    return jsonify({
        "version": "1.0.0",
        "contributors": ["Dami-lowdev", "Reine Brenda Ankoume", "Corel Chouamou"],
        "endpoints": ["/api/events", "/api/news", "/api/faq", "/healthz", "/readyz"]
    }), 200

# ---------------------------------------------------------------------------
# Interface web minimale
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Content Platform</title>
  <style>
    body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
    h1 { color: #333; }
    .card { background: white; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
    .badge { display: inline-block; background: #4CAF50; color: white; border-radius: 4px; padding: 2px 8px; font-size: 12px; }
    .badge.error { background: #f44336; }
    ul { padding-left: 20px; }
    li { margin: 6px 0; }
    a { color: #1976D2; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>Content Platform</h1>
  <p>Plateforme de diffusion de contenu statique cloud-native.</p>

  <div class="card">
    <h2>Endpoints disponibles</h2>
    <ul>
      <li><a href="/api/events">/api/events</a> — Événements</li>
      <li><a href="/api/news">/api/news</a> — Actualités</li>
      <li><a href="/api/faq">/api/faq</a> — FAQ</li>
      <li><a href="/healthz">/healthz</a> — Liveness probe</li>
      <li><a href="/readyz">/readyz</a> — Readiness probe</li>
    </ul>
  </div>

  <div class="card">
    <h2>Statut</h2>
    <p>Cache TTL : <strong>{{ cache_ttl }}s</strong></p>
    <p>Container Blob : <strong>{{ container }}</strong></p>
    <p>Azure connecté : 
      {% if connected %}
        <span class="badge">OK</span>
      {% else %}
        <span class="badge error">Non configuré</span>
      {% endif %}
    </p>
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(
        HTML_TEMPLATE,
        cache_ttl=CACHE_TTL,
        container=CONTAINER_NAME,
        connected=bool(AZURE_CONNECTION_STRING),
    )


# ---------------------------------------------------------------------------
# Point d'entrée local
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)