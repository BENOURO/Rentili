import pytest
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture(autouse=True)
def _isolation(settings, tmp_path):
    """Fichiers envoyés (photos de profil) dans un dossier temporaire, et cache vidé entre les tests."""
    from django.core.cache import cache

    settings.MEDIA_ROOT = tmp_path
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def member(db):
    return User.objects.create_user("olfa@test.tn", "pass-12345", first_name="Olfa", last_name="Ben Ali", city="Tunis")


@pytest.fixture
def other(db):
    return User.objects.create_user("rami@test.tn", "pass-12345", first_name="Rami", last_name="Saidi", city="Sfax")


@pytest.fixture
def auth(api, member):
    """Client connecté en tant que `member` (jeton JWT dans l'en-tête Authorization)."""
    r = api.post("/api/auth/login/", {"email": "olfa@test.tn", "password": "pass-12345"}, format="json")
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    api.refresh_token = r.data["refresh"]
    return api
