"""Tests de l'API du module « Gestion des utilisateurs » — Sprint 1 (US01 à US06)."""

import io

import pytest
from PIL import Image

from users.models import User
from users.signals import user_deleted

STRONG = "un-mot-de-passe-solide"


def register(api, **extra):
    data = {"email": "Lina@Test.tn", "password": STRONG, "first_name": "Lina", "last_name": "Ayari", "city": "Tunis", **extra}
    return api.post("/api/auth/register/", data, format="json")


# ---------- US01 : inscription ----------
def test_register_returns_tokens_and_profile(api, db):
    r = register(api)
    assert r.status_code == 201 and r.data["access"] and r.data["refresh"]
    assert r.data["user"]["email"] == "lina@test.tn" and r.data["user"]["city"] == "Tunis"
    assert "password" not in r.data["user"]


def test_password_is_hashed(api, db):
    register(api)
    assert User.objects.get().password.startswith("pbkdf2_")


def test_duplicate_email_rejected_case_insensitive(api, member):
    r = register(api, email="OLFA@test.tn")
    assert r.status_code == 400 and "email" in r.data


@pytest.mark.parametrize("password", ["court", "12345678901", "password123"])
def test_weak_passwords_rejected(api, db, password):
    r = register(api, password=password)
    assert r.status_code == 400 and "password" in r.data


def test_names_required(api, db):
    assert register(api, first_name="").status_code == 400


# ---------- US02 : connexion / déconnexion ----------
def test_login_with_email_case_insensitive(api, member):
    r = api.post("/api/auth/login/", {"email": "OLFA@test.tn", "password": "pass-12345"}, format="json")
    assert r.status_code == 200 and r.data["user"]["first_name"] == "Olfa"


def test_wrong_password_rejected_with_clear_message(api, member):
    r = api.post("/api/auth/login/", {"email": "olfa@test.tn", "password": "faux"}, format="json")
    assert r.status_code == 401 and "incorrect" in str(r.data["detail"])


def test_protected_endpoint_needs_token(api, db):
    assert api.get("/api/users/me/").status_code == 401


def test_refresh_gives_new_access_token(auth):
    r = auth.post("/api/auth/refresh/", {"refresh": auth.refresh_token}, format="json")
    assert r.status_code == 200 and r.data["access"]


# ---------- US03 / US04 : consulter et modifier son profil ----------
def test_me_returns_private_profile(auth):
    r = auth.get("/api/users/me/")
    assert r.status_code == 200 and r.data["email"] == "olfa@test.tn" and r.data["city"] == "Tunis"


def test_patch_profile(auth, member):
    r = auth.patch("/api/users/me/", {"city": "Sousse", "bio": "Bricoleuse", "phone": "+216 20 000 000"}, format="json")
    assert r.status_code == 200 and r.data["city"] == "Sousse" and r.data["bio"] == "Bricoleuse"


def test_email_and_staff_flag_are_read_only(auth, member):
    auth.patch("/api/users/me/", {"email": "pirate@test.tn", "is_staff": True}, format="json")
    member.refresh_from_db()
    assert member.email == "olfa@test.tn" and not member.is_staff


def test_upload_avatar(auth, member):
    buf = io.BytesIO(); Image.new("RGB", (40, 40), "red").save(buf, "PNG"); buf.seek(0); buf.name = "a.png"
    r = auth.patch("/api/users/me/", {"avatar": buf}, format="multipart")
    assert r.status_code == 200 and "avatars/" in r.data["avatar"]


def test_cannot_blank_required_names(auth):
    assert auth.patch("/api/users/me/", {"first_name": ""}, format="json").status_code == 400


# ---------- US05 : profil public ----------
def test_public_profile_hides_private_data(api, member):
    member.phone = "+216 20 000 000"; member.save()
    r = api.get(f"/api/users/{member.pk}/")
    assert r.status_code == 200 and r.data["display_name"] == "Olfa B."
    assert not {"email", "phone", "last_name"} & set(r.data)


def test_member_list_is_public(api, member, other):
    r = api.get("/api/users/")
    assert r.status_code == 200 and r.data["count"] == 2
    assert not {"email", "phone"} & set(r.data["results"][0])


def test_staff_and_deleted_members_hidden(api, member, other):
    User.objects.create_superuser("admin@test.tn", "pass-12345")
    other.anonymize()
    r = api.get("/api/users/")
    assert [u["first_name"] for u in r.data["results"]] == ["Olfa"]
    assert api.get(f"/api/users/{other.pk}/").status_code == 404


# ---------- US06 : supprimer son compte ----------
def test_delete_account_anonymizes_and_blocks_login(auth, member, api):
    assert auth.delete("/api/users/me/").status_code == 204
    member.refresh_from_db()
    assert not member.is_active and member.deleted_at and member.first_name == "Utilisateur"
    assert not member.has_usable_password() and member.email != "olfa@test.tn"
    api.credentials()
    assert api.post("/api/auth/login/", {"email": "olfa@test.tn", "password": "pass-12345"}, format="json").status_code == 401
    assert register(api, email="olfa@test.tn").status_code == 201  # l'email redevient libre


def test_delete_sends_signal_for_other_modules(auth):
    received = []
    handler = lambda sender, user, **kw: received.append(user.email)  # noqa: E731
    user_deleted.connect(handler)
    try:
        auth.delete("/api/users/me/")
    finally:
        user_deleted.disconnect(handler)
    assert received == ["olfa@test.tn"]


def test_deleted_users_token_stops_working(auth):
    auth.delete("/api/users/me/")
    assert auth.get("/api/users/me/").status_code == 401  # compte inactif : jeton refusé
