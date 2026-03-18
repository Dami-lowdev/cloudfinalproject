# Content Platform — Cloud Native

Plateforme de diffusion de contenu statique cloud-native déployée sur Azure Kubernetes Service.

## Stack technique

- **Backend** : Python 3 / Flask
- **Stockage** : Azure Blob Storage (JSON/YAML)
- **Conteneurisation** : Docker
- **Orchestration** : Azure Kubernetes Service (AKS)
- **Registry** : GitHub Container Registry (GHCR)
- **CI/CD** : GitHub Actions

## Endpoints disponibles

| Endpoint | Méthode | Description |
|---|---|---|
| `/api/events` | GET | Retourne les événements |
| `/api/news` | GET | Retourne les actualités |
| `/api/faq` | GET | Retourne la FAQ |
| `/healthz` | GET | Liveness probe |
| `/readyz` | GET | Readiness probe |

## Structure du projet

```
content-platform/
├── app/                    # Code source Flask
│   ├── app.py
│   ├── requirements.txt
│   └── tests/
│       └── test_app.py
├── data/                   # Fichiers JSON uploadés sur Azure Blob Storage
│   ├── events.json
│   ├── news.json
│   └── faq.json
├── k8s/                    # Manifests Kubernetes
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secret.yaml
├── .github/
│   └── workflows/
│       └── ci-cd.yaml      # Pipeline GitHub Actions
├── Dockerfile
├── .gitignore
└── README.md
```

## Lancer en local

### 1. Créer et activer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate      # Linux / macOS
# ou
venv\Scripts\activate         # Windows
```

> Le venv isole les dépendances du projet sans affecter l'environnement Python global.

### 2. Installer les dépendances

```bash
pip install -r app/requirements.txt
```

### 3. Configurer les variables d'environnement (optionnel en local)

```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;"
export AZURE_CONTAINER_NAME="content"
export CACHE_TTL=60
```

Sans ces variables, l'app démarre quand même — `/healthz` répond `ok`, `/readyz` répond `not ready`.

### 4. Lancer l'application

```bash
cd app
python app.py
```

L'application est disponible sur `http://localhost:5000`.

### 5. Vérifier les health checks

```bash
curl http://localhost:5000/healthz
# {"status": "ok", "timestamp": "..."}

curl http://localhost:5000/readyz
# {"status": "ready", ...}  si Azure est configuré
# {"status": "not ready", ...}  si pas de connection string
```

## Lancer les tests

```bash
# Depuis la racine du projet, avec le venv activé
cd app
pytest tests/ -v
```

Les tests utilisent des mocks — **aucune connexion Azure n'est requise** pour les exécuter.

## Désactiver l'environnement virtuel

```bash
deactivate
```

## Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string Azure Blob | *(requis en prod)* |
| `AZURE_CONTAINER_NAME` | Nom du container Blob | `content` |
| `CACHE_TTL` | Durée du cache mémoire en secondes | `60` |

## Stratégie Git

**Trunk-based development** : une branche `main` principale, branches de feature courtes mergées rapidement.

```
main
 ├── feat/flask-app
 ├── feat/dockerfile
 ├── feat/aks-manifests
 └── feat/ci-cd
```

Chaque merge sur `main` déclenche automatiquement le pipeline CI/CD.