import json
import pytest
from unittest.mock import patch, MagicMock

# On importe l'app Flask en mode test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Client de test Flask — pas de serveur réel nécessaire."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_cache():
    """Vide le cache avant chaque test pour garantir l'isolation."""
    cache.clear()
    yield
    cache.clear()


# Données de mock réutilisables
MOCK_EVENTS = {"items": [{"id": 1, "title": "Conférence Cloud", "date": "2026-04-15"}]}
MOCK_NEWS   = {"items": [{"id": 1, "title": "Lancement v1.0",   "date": "2026-03-18"}]}
MOCK_FAQ    = {"items": [{"id": 1, "question": "Comment accéder à l'API ?", "answer": "Via GET /api/..."}]}


def make_blob_mock(data: dict):
    """
    Construit un mock BlobServiceClient qui retourne `data` sérialisé en JSON
    lors de l'appel download_blob().readall().
    """
    mock_blob = MagicMock()
    mock_blob.download_blob.return_value.readall.return_value = json.dumps(data).encode("utf-8")

    mock_container = MagicMock()
    mock_container.get_blob_client.return_value = mock_blob

    mock_service = MagicMock()
    mock_service.get_blob_client.return_value = mock_blob
    return mock_service


# ---------------------------------------------------------------------------
# Tests de santé (Health checks)
# ---------------------------------------------------------------------------

class TestHealthChecks:

    def test_healthz_status_200(self, client):
        """GET /healthz doit retourner HTTP 200."""
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_healthz_json_valide(self, client):
        """GET /healthz doit retourner du JSON valide."""
        response = client.get("/healthz")
        data = response.get_json()
        assert data is not None

    def test_healthz_champ_status(self, client):
        """GET /healthz doit contenir le champ 'status' avec la valeur 'ok'."""
        response = client.get("/healthz")
        data = response.get_json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_healthz_champ_timestamp(self, client):
        """GET /healthz doit contenir un champ 'timestamp'."""
        response = client.get("/healthz")
        data = response.get_json()
        assert "timestamp" in data

    def test_readyz_status_200_sans_azure(self, client):
        """GET /readyz sans Azure configuré doit retourner HTTP 503."""
        with patch.dict(os.environ, {}, clear=False):
            # On s'assure que la connection string est vide
            os.environ.pop("AZURE_STORAGE_CONNECTION_STRING", None)
            # Recharge la variable dans l'app
            import app as app_module
            app_module.AZURE_CONNECTION_STRING = ""
            response = client.get("/readyz")
            assert response.status_code == 503

    def test_readyz_json_valide(self, client):
        """GET /readyz doit retourner du JSON valide."""
        response = client.get("/readyz")
        data = response.get_json()
        assert data is not None

    def test_readyz_champ_status(self, client):
        """GET /readyz doit contenir le champ 'status'."""
        response = client.get("/readyz")
        data = response.get_json()
        assert "status" in data

    def test_readyz_pret_avec_azure(self, client):
        """GET /readyz doit retourner 'ready' quand Azure est configuré."""
        import app as app_module
        app_module.AZURE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=dGVzdA==;EndpointSuffix=core.windows.net"
        response = client.get("/readyz")
        data = response.get_json()
        assert response.status_code == 200
        assert data["status"] == "ready"
        # Remise à zéro après le test
        app_module.AZURE_CONNECTION_STRING = ""


# ---------------------------------------------------------------------------
# Tests fonctionnels — /api/events
# ---------------------------------------------------------------------------

class TestEventsEndpoint:

    @patch("app.get_blob_client")
    def test_events_status_200(self, mock_get_client, client):
        """GET /api/events doit retourner HTTP 200."""
        mock_get_client.return_value = make_blob_mock(MOCK_EVENTS)
        response = client.get("/api/events")
        assert response.status_code == 200

    @patch("app.get_blob_client")
    def test_events_json_valide(self, mock_get_client, client):
        """GET /api/events doit retourner du JSON valide."""
        mock_get_client.return_value = make_blob_mock(MOCK_EVENTS)
        response = client.get("/api/events")
        data = response.get_json()
        assert data is not None

    @patch("app.get_blob_client")
    def test_events_contient_items(self, mock_get_client, client):
        """GET /api/events doit retourner une clé 'items' contenant une liste."""
        mock_get_client.return_value = make_blob_mock(MOCK_EVENTS)
        response = client.get("/api/events")
        data = response.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @patch("app.get_blob_client")
    def test_events_structure_item(self, mock_get_client, client):
        """Chaque item events doit avoir les champs id, title, date."""
        mock_get_client.return_value = make_blob_mock(MOCK_EVENTS)
        response = client.get("/api/events")
        items = response.get_json()["items"]
        assert len(items) > 0
        assert "id" in items[0]
        assert "title" in items[0]

    @patch("app.get_blob_client")
    def test_events_erreur_blob(self, mock_get_client, client):
        """GET /api/events doit retourner 500 si Azure Blob est inaccessible."""
        mock_get_client.side_effect = Exception("Blob inaccessible")
        response = client.get("/api/events")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# Tests fonctionnels — /api/news
# ---------------------------------------------------------------------------

class TestNewsEndpoint:

    @patch("app.get_blob_client")
    def test_news_status_200(self, mock_get_client, client):
        """GET /api/news doit retourner HTTP 200."""
        mock_get_client.return_value = make_blob_mock(MOCK_NEWS)
        response = client.get("/api/news")
        assert response.status_code == 200

    @patch("app.get_blob_client")
    def test_news_json_valide(self, mock_get_client, client):
        """GET /api/news doit retourner du JSON valide."""
        mock_get_client.return_value = make_blob_mock(MOCK_NEWS)
        response = client.get("/api/news")
        assert response.get_json() is not None

    @patch("app.get_blob_client")
    def test_news_contient_items(self, mock_get_client, client):
        """GET /api/news doit retourner une clé 'items' contenant une liste."""
        mock_get_client.return_value = make_blob_mock(MOCK_NEWS)
        response = client.get("/api/news")
        data = response.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @patch("app.get_blob_client")
    def test_news_erreur_blob(self, mock_get_client, client):
        """GET /api/news doit retourner 500 si Azure Blob est inaccessible."""
        mock_get_client.side_effect = Exception("Blob inaccessible")
        response = client.get("/api/news")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# Tests fonctionnels — /api/faq
# ---------------------------------------------------------------------------

class TestFaqEndpoint:

    @patch("app.get_blob_client")
    def test_faq_status_200(self, mock_get_client, client):
        """GET /api/faq doit retourner HTTP 200."""
        mock_get_client.return_value = make_blob_mock(MOCK_FAQ)
        response = client.get("/api/faq")
        assert response.status_code == 200

    @patch("app.get_blob_client")
    def test_faq_json_valide(self, mock_get_client, client):
        """GET /api/faq doit retourner du JSON valide."""
        mock_get_client.return_value = make_blob_mock(MOCK_FAQ)
        response = client.get("/api/faq")
        assert response.get_json() is not None

    @patch("app.get_blob_client")
    def test_faq_contient_items(self, mock_get_client, client):
        """GET /api/faq doit retourner une clé 'items' contenant une liste."""
        mock_get_client.return_value = make_blob_mock(MOCK_FAQ)
        response = client.get("/api/faq")
        data = response.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    @patch("app.get_blob_client")
    def test_faq_structure_item(self, mock_get_client, client):
        """Chaque item faq doit avoir les champs question et answer."""
        mock_get_client.return_value = make_blob_mock(MOCK_FAQ)
        response = client.get("/api/faq")
        items = response.get_json()["items"]
        assert len(items) > 0
        assert "question" in items[0]
        assert "answer" in items[0]

    @patch("app.get_blob_client")
    def test_faq_erreur_blob(self, mock_get_client, client):
        """GET /api/faq doit retourner 500 si Azure Blob est inaccessible."""
        mock_get_client.side_effect = Exception("Blob inaccessible")
        response = client.get("/api/faq")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# Test du cache TTL
# ---------------------------------------------------------------------------

class TestCache:

    @patch("app.get_blob_client")
    def test_cache_evite_double_appel_blob(self, mock_get_client, client):
        """Le cache doit éviter un second appel à Azure Blob."""
        mock_get_client.return_value = make_blob_mock(MOCK_EVENTS)
        client.get("/api/events")
        client.get("/api/events")
        # get_blob_client ne doit avoir été appelé qu'une seule fois
        assert mock_get_client.call_count == 1