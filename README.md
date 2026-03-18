# Content Platform — Cloud Native

Plateforme de diffusion de contenu statique cloud-native déployée sur Azure Kubernetes Service.

## Stack technique
- **Backend** : Python / Flask
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
├── app/                  # Code source Flask
│   ├── app.py
│   ├── requirements.txt
│   └── tests/
├── k8s/                  # Manifests Kubernetes
├── .github/workflows/    # Pipeline CI/CD
├── data/                 # Fichiers JSON de test
└── Dockerfile
```

## Lancer en local

```bash
pip install -r app/requirements.txt
cd app && python app.py
```

## Lancer les tests

```bash
cd app && pytest tests/ -v
```

## Stratégie Git

Trunk-based development : une branche `main` principale, branches de feature courtes (`feat/xxx`) mergées rapidement.