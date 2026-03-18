# conftest.py — Configuration partagee pour les tests pytest

import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="session")
def base_url():
    """URL de base pour les tests d'integration."""
    return "http://localhost:5000"


@pytest.fixture(scope="session")
def api_prefix():
    """Prefixe des endpoints API."""
    return "/api"