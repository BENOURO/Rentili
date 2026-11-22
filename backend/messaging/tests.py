"""Tests de la messagerie (US37 à US40) : API REST, diffusion temps réel et WebSocket.

Les fixtures `api`, `auth` (connecté en tant que `member`), `member` et `other` viennent du conftest.py racine.
"""

from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from messaging import services
from messaging.middleware import JWTAuthMiddleware
from messaging.models import Conversation, Message
from messaging.routing import websocket_urlpatterns
from users.models import User

BASE = "/api/messaging"
INBOX = f"{BASE}/conversations/"
LISTING = {"listing_id": 7, "listing_title": "Perceuse Bosch"}


# ---------- outils ----------
class FakeLayer:
    """Couche de canaux factice : mémorise ce qui est diffusé au lieu de l'envoyer."""

    def __init__(self):
        self.sent = []

    async def group_send(self, group, message):
        self.sent.append((group, message))

    def events(self, user):
        """Charges utiles reçues par le groupe WebSocket d'un utilisateur, dans l'ordre."""
        return [m["payload"] for g, m in self.sent if g == f"user_{user.pk}"]


@pytest.fixture
def layer(monkeypatch):
    fake = FakeLayer()
    monkeypatch.setattr(services, "get_channel_layer", lambda: fake)
    return fake


@pytest.fixture
def third(db):
    return User.objects.create_user("sami@test.tn", "pass-12345", first_name="Sami", last_name="Trabelsi", city="Sousse")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def auth_other(other):
    return client_for(other)


@pytest.fixture
def auth_third(third):
    return client_for(third)


def make_conversation(starter, recipient, listing_id=7):
    return Conversation.objects.create(starter=starter, recipient=recipient, listing_id=listing_id, listing_title="Perceuse Bosch")


def make_message(conversation, sender, body="Bonjour"):
    return Message.objects.create(conversation=conversation, sender=sender, body=body)


def start(client, to, body="Bonjour, est-elle disponible ?", **extra):
    data = {"recipient": to.pk, **LISTING, "body": body, **extra}
    return client.post(INBOX, data, format="json")


def thread(conversation):
    return f"{BASE}/conversations/{conversation.pk}/messages/"


def one(message):
    return f"{BASE}/messages/{message.pk}/"


# ---------- US37 : envoyer un message ----------
def test_start_conversation_creates_thread_and_first_message(auth, member, other):
    r = start(auth, other)
    assert r.status_code == 201
    conv, msg = r.data["conversation"], r.data["message"]
    assert conv["listing_id"] == 7 and conv["listing_title"] == "Perceuse Bosch"
    assert conv["other"]["display_name"] == "Rami S." and conv["unread_count"] == 0
    assert conv["last_message"]["body"] == msg["body"] == "Bonjour, est-elle disponible ?"
    assert msg["sender"] == member.pk and msg["read_at"] is None and msg["is_deleted"] is False
    assert Conversation.objects.count() == 1 and Message.objects.count() == 1


def test_second_message_reuses_the_conversation(auth, other):
    first = start(auth, other).data["conversation"]["id"]
    second = start(auth, other, "Et le week-end ?").data["conversation"]["id"]
    assert first == second
    assert Conversation.objects.count() == 1 and Message.objects.count() == 2


def test_conversation_is_shared_in_both_directions(auth, auth_other, member, other):
    first = start(auth, other).data["conversation"]["id"]
    answer = start(auth_other, member, "Oui, elle est libre.")
    assert answer.status_code == 201 and answer.data["conversation"]["id"] == first
    assert Conversation.objects.count() == 1


def test_another_listing_opens_another_conversation(auth, other):
    start(auth, other, listing_id=7)
    start(auth, other, listing_id=8)
    assert Conversation.objects.count() == 2


def test_listing_title_is_optional(auth, other):
    r = auth.post(INBOX, {"recipient": other.pk, "listing_id": 3, "body": "Bonjour"}, format="json")
    assert r.status_code == 201 and r.data["conversation"]["listing_title"] == ""


def test_cannot_write_to_yourself(auth, member):
    r = start(auth, member)
    assert r.status_code == 400 and "vous-même" in str(r.data["recipient"])
    assert not Conversation.objects.exists()


def test_unknown_recipient_rejected(auth):
    r = auth.post(INBOX, {"recipient": 9999, **LISTING, "body": "Bonjour"}, format="json")
    assert r.status_code == 400 and "recipient" in r.data


def test_deleted_member_cannot_be_contacted(auth, other):
    other.anonymize()
    r = start(auth, other)
    assert r.status_code == 400 and "recipient" in r.data
    assert not Conversation.objects.exists()


def test_empty_message_rejected(auth, other):
    for body in ("", "   "):
        r = start(auth, other, body)
        assert r.status_code == 400 and r.data["body"][0] == "Le message ne peut pas être vide."
    assert not Message.objects.exists()


def test_message_longer_than_2000_characters_rejected(auth, other):
    r = start(auth, other, "x" * 2001)
    assert r.status_code == 400 and "2000" in str(r.data["body"])
    assert start(auth, other, "x" * 2000).status_code == 201


@pytest.mark.parametrize("field", ["listing_id", "recipient"])
def test_ids_must_be_positive(auth, other, field):
    r = start(auth, other, **{field: 0})
    assert r.status_code == 400 and field in r.data


def test_reply_inside_an_existing_conversation(auth, auth_other, member, other):
    conv = make_conversation(member, other)
    r = auth_other.post(thread(conv), {"body": "Avec plaisir"}, format="json")
    assert r.status_code == 201 and r.data["sender"] == other.pk and r.data["conversation"] == conv.pk
    assert [m["body"] for m in auth.get(thread(conv)).data["results"]] == ["Avec plaisir"]


def test_reply_rejects_empty_body(auth, member, other):
    conv = make_conversation(member, other)
    assert auth.post(thread(conv), {"body": ""}, format="json").status_code == 400


def test_cannot_write_to_a_member_who_deleted_the_account(auth, member, other):
    conv = make_conversation(member, other)
    make_message(conv, other, "Avant ma suppression")
    other.anonymize()
    r = auth.post(thread(conv), {"body": "Allô ?"}, format="json")
    assert r.status_code == 403 and "supprimé" in str(r.data["detail"])
    assert auth.get(thread(conv)).status_code == 200  # l'historique reste consultable


# ---------- US38 : boîte de réception, fil, lecture ----------
def test_inbox_only_lists_my_conversations(auth, member, other, third):
    mine = make_conversation(member, other, 1)
    make_conversation(other, third, 2)
    r = auth.get(INBOX)
    assert r.status_code == 200 and r.data["count"] == 1 and r.data["results"][0]["id"] == mine.pk


def test_inbox_shows_the_other_member_last_message_and_unread_count(auth, auth_other, member, other):
    conv = make_conversation(member, other)
    make_message(conv, other, "a")
    make_message(conv, other, "b")
    make_message(conv, member, "c")
    mine = auth.get(INBOX).data["results"][0]
    assert mine["other"]["display_name"] == "Rami S." and mine["unread_count"] == 2
    assert mine["last_message"]["body"] == "c"
    theirs = auth_other.get(INBOX).data["results"][0]
    assert theirs["other"]["display_name"] == "Olfa B." and theirs["unread_count"] == 1
    assert not {"email", "phone"} & set(mine["other"])  # profil public uniquement


def test_inbox_ignores_deleted_messages_in_unread_count(auth, member, other):
    conv = make_conversation(member, other)
    gone = make_message(conv, other, "oups")
    make_message(conv, other, "reste")
    gone.deleted_at = timezone.now()
    gone.save()
    assert auth.get(INBOX).data["results"][0]["unread_count"] == 1


def test_inbox_most_recent_conversation_first(auth, member, other, third):
    a, b = make_conversation(member, other, 1), make_conversation(member, third, 2)
    old = timezone.now() - timedelta(days=2)
    Conversation.objects.filter(pk=a.pk).update(updated_at=old)
    Conversation.objects.filter(pk=b.pk).update(updated_at=old + timedelta(days=1))
    assert [c["id"] for c in auth.get(INBOX).data["results"]] == [b.pk, a.pk]
    assert start(auth, other, "Du nouveau", listing_id=1).status_code == 201  # réveille la conversation a
    assert [c["id"] for c in auth.get(INBOX).data["results"]] == [a.pk, b.pk]


def test_conversation_without_message_has_no_last_message(auth, member, other):
    make_conversation(member, other)
    assert auth.get(INBOX).data["results"][0]["last_message"] is None


def test_conversation_detail(auth, member, other):
    conv = make_conversation(member, other)
    make_message(conv, other, "Salut")
    r = auth.get(f"{BASE}/conversations/{conv.pk}/")
    assert r.status_code == 200 and r.data["listing_title"] == "Perceuse Bosch"
    assert r.data["other"]["id"] == other.pk and r.data["unread_count"] == 1


def test_thread_is_chronological_and_paginated_by_50(auth, member, other):
    conv = make_conversation(member, other)
    Message.objects.bulk_create([Message(conversation=conv, sender=other, body=f"m{i}") for i in range(55)])
    page = auth.get(thread(conv)).data
    assert len(page["results"]) == 50 and page["has_more"] is True
    assert page["results"][0]["body"] == "m5" and page["results"][-1]["body"] == "m54"
    older = auth.get(f"{thread(conv)}?before={page['results'][0]['id']}").data
    assert [m["body"] for m in older["results"]] == ["m0", "m1", "m2", "m3", "m4"] and older["has_more"] is False
    assert len(auth.get(f"{thread(conv)}?before=abc").data["results"]) == 50  # paramètre invalide ignoré


def test_thread_shows_deleted_messages_without_their_text(auth, member, other):
    conv = make_conversation(member, other)
    gone = make_message(conv, other, "secret")
    gone.body, gone.deleted_at = "", timezone.now()
    gone.save()
    [msg] = auth.get(thread(conv)).data["results"]
    assert msg["is_deleted"] is True and msg["body"] == ""


def test_mark_read_only_marks_received_messages(auth, member, other):
    conv = make_conversation(member, other)
    mine = make_message(conv, member, "envoyé par moi")
    a, b = make_message(conv, other, "1"), make_message(conv, other, "2")
    url = f"{BASE}/conversations/{conv.pk}/read/"
    r = auth.post(url)
    assert r.status_code == 200 and r.data == {"marked": 2}
    for m in (mine, a, b):
        m.refresh_from_db()
    assert a.read_at and b.read_at and mine.read_at is None
    assert auth.post(url).data == {"marked": 0}


def test_unread_count_endpoint(auth, member, other, third):
    c1, c2, unrelated = make_conversation(member, other, 1), make_conversation(third, member, 2), make_conversation(other, third, 3)
    make_message(c1, other)
    make_message(c1, other)
    make_message(c2, third)
    make_message(c1, member)  # mes propres messages ne comptent pas
    make_message(unrelated, other)  # ni ceux des conversations des autres
    gone = make_message(c2, third, "x")
    gone.deleted_at = timezone.now()
    gone.save()
    r = auth.get(f"{BASE}/unread-count/")
    assert r.status_code == 200 and r.data == {"count": 3}
    auth.post(f"{BASE}/conversations/{c1.pk}/read/")
    assert auth.get(f"{BASE}/unread-count/").data == {"count": 1}


def test_outsider_cannot_see_or_touch_a_conversation(auth_third, member, other):
    conv = make_conversation(member, other)
    msg = make_message(conv, member)
    assert auth_third.get(f"{BASE}/conversations/{conv.pk}/").status_code == 404
    assert auth_third.get(thread(conv)).status_code == 404
    assert auth_third.post(thread(conv), {"body": "Coucou"}, format="json").status_code == 404
    assert auth_third.post(f"{BASE}/conversations/{conv.pk}/read/").status_code == 404
    assert auth_third.patch(one(msg), {"body": "piraté"}, format="json").status_code == 404
    assert auth_third.delete(one(msg)).status_code == 404
    msg.refresh_from_db()
    assert msg.body == "Bonjour" and not msg.is_deleted


@pytest.mark.parametrize("method,path", [
    ("get", "/conversations/"), ("post", "/conversations/"), ("get", "/conversations/1/"),
    ("get", "/conversations/1/messages/"), ("post", "/conversations/1/messages/"), ("post", "/conversations/1/read/"),
    ("patch", "/messages/1/"), ("delete", "/messages/1/"), ("get", "/unread-count/"),
])
def test_every_endpoint_requires_a_token(api, db, method, path):
    assert getattr(api, method)(BASE + path).status_code == 401


# ---------- US39 : modifier son message ----------
def test_edit_own_message(auth, member, other):
    msg = make_message(make_conversation(member, other), member, "avant")
    r = auth.patch(one(msg), {"body": "après"}, format="json")
    assert r.status_code == 200 and r.data["body"] == "après" and r.data["edited_at"]
    msg.refresh_from_db()
    assert msg.body == "après" and msg.edited_at


def test_cannot_edit_someone_elses_message(auth, member, other):
    msg = make_message(make_conversation(member, other), other, "à moi")
    r = auth.patch(one(msg), {"body": "à toi"}, format="json")
    assert r.status_code == 403 and "propres" in str(r.data["detail"])
    msg.refresh_from_db()
    assert msg.body == "à moi" and msg.edited_at is None


def test_cannot_edit_a_deleted_message(auth, member, other):
    msg = make_message(make_conversation(member, other), member)
    assert auth.delete(one(msg)).status_code == 204
    r = auth.patch(one(msg), {"body": "ressuscité"}, format="json")
    assert r.status_code == 400 and "supprimé" in str(r.data["detail"])


def test_edit_rejects_empty_body(auth, member, other):
    msg = make_message(make_conversation(member, other), member, "intact")
    assert auth.patch(one(msg), {"body": ""}, format="json").status_code == 400
    msg.refresh_from_db()
    assert msg.body == "intact"


# ---------- US40 : supprimer son message ----------
def test_delete_own_message_is_a_soft_delete(auth, member, other):
    conv = make_conversation(member, other)
    msg = make_message(conv, member, "à effacer")
    assert auth.delete(one(msg)).status_code == 204
    msg.refresh_from_db()
    assert msg.body == "" and msg.deleted_at and msg.is_deleted
    assert Message.objects.filter(pk=msg.pk).exists()  # la ligne reste : l'historique garde la trace
    assert auth.get(thread(conv)).data["results"][0]["is_deleted"] is True


def test_cannot_delete_someone_elses_message(auth, member, other):
    msg = make_message(make_conversation(member, other), other, "pas touche")
    r = auth.delete(one(msg))
    assert r.status_code == 403 and "propres" in str(r.data["detail"])
    msg.refresh_from_db()
    assert msg.body == "pas touche" and not msg.is_deleted


def test_deleting_twice_is_harmless_and_broadcast_once(auth, member, other, layer, django_capture_on_commit_callbacks):
    msg = make_message(make_conversation(member, other), member)
    with django_capture_on_commit_callbacks(execute=True):
        assert auth.delete(one(msg)).status_code == 204
    first, sent = Message.objects.get(pk=msg.pk).deleted_at, len(layer.sent)
    assert sent == 2
    with django_capture_on_commit_callbacks(execute=True):
        assert auth.delete(one(msg)).status_code == 204
    assert Message.objects.get(pk=msg.pk).deleted_at == first and len(layer.sent) == sent


# ---------- diffusion en temps réel (services) ----------
def test_new_message_is_broadcast_to_both_participants_only_after_commit(member, other, layer, django_capture_on_commit_callbacks):
    conv = make_conversation(member, other)
    with django_capture_on_commit_callbacks() as callbacks:
        message = services.send_message(conv, member, "Salut")
    assert layer.sent == []  # rien n'est parti tant que la transaction n'est pas validée
    assert len(callbacks) == 1
    callbacks[0]()
    assert {group for group, _ in layer.sent} == {f"user_{member.pk}", f"user_{other.pk}"}
    assert all(m["type"] == "chat.event" for _, m in layer.sent)
    [payload] = layer.events(other)
    assert payload["event"] == "message.created" and payload["conversation"] == conv.pk
    assert payload["message"]["id"] == message.pk and payload["message"]["body"] == "Salut"


def test_rolled_back_transaction_broadcasts_nothing(member, other, layer, django_capture_on_commit_callbacks):
    conv = make_conversation(member, other)
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(RuntimeError), transaction.atomic():
            services.send_message(conv, member, "annulé")
            raise RuntimeError("échec après l'envoi")
    assert callbacks == [] and layer.sent == []
    assert not Message.objects.exists()


def test_start_conversation_broadcasts_after_commit(member, other, layer, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        conv, message = services.start_conversation(member, other.pk, 7, "Perceuse Bosch", "Bonjour")
    assert [p["event"] for p in layer.events(other)] == ["message.created"]
    assert layer.events(other)[0]["conversation"] == conv.pk and message.conversation_id == conv.pk


def test_edit_delete_and_read_events_are_broadcast(auth, member, other, layer, django_capture_on_commit_callbacks):
    conv = make_conversation(member, other)
    mine, theirs = make_message(conv, member, "v1"), make_message(conv, other, "salut")
    with django_capture_on_commit_callbacks(execute=True):
        auth.patch(one(mine), {"body": "v2"}, format="json")
        auth.delete(one(mine))
        auth.post(f"{BASE}/conversations/{conv.pk}/read/")
    updated, deleted, read = layer.events(other)
    assert updated["event"] == "message.updated" and updated["message"]["body"] == "v2"
    assert deleted["event"] == "message.deleted" and deleted["message"]["is_deleted"] is True
    assert read["event"] == "messages.read" and read["reader"] == member.pk and read["message_ids"] == [theirs.pk] and read["read_at"]
    assert layer.events(member) == layer.events(other)  # les deux participants reçoivent les mêmes événements


def test_missing_channel_layer_is_tolerated(member, other, monkeypatch, django_capture_on_commit_callbacks):
    monkeypatch.setattr(services, "get_channel_layer", lambda: None)
    conv = make_conversation(member, other)
    with django_capture_on_commit_callbacks() as callbacks:
        assert services.send_message(conv, member, "sans WebSocket").pk
    assert callbacks == []


# ---------- modèles ----------
def test_conversation_helpers(member, other, third):
    conv = make_conversation(member, other)
    assert conv.has_participant(member) and conv.has_participant(other) and not conv.has_participant(third)
    assert conv.other_for(member) == other and conv.other_for(other) == member
    assert str(conv) == f"#{conv.pk} · annonce 7"


def test_message_helpers(member, other):
    msg = make_message(make_conversation(member, other), member)
    assert str(msg) == f"Message {msg.pk} de {member.pk}" and not msg.is_deleted
    msg.deleted_at = timezone.now()
    assert msg.is_deleted


def test_database_refuses_self_conversation(member):
    with pytest.raises(IntegrityError), transaction.atomic():
        Conversation.objects.create(starter=member, recipient=member, listing_id=1)


def test_database_refuses_duplicate_conversation(member, other):
    make_conversation(member, other)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_conversation(member, other)


# ---------- WebSocket ----------
def token_for(user):
    return str(AccessToken.for_user(user))


def ws(token=None):
    """Client WebSocket de test sur la pile de l'application : authentification JWT puis routeur."""
    app = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
    return WebsocketCommunicator(app, "/ws/messaging/" + (f"?token={token}" if token is not None else ""))


def websocket_test(fn):
    return pytest.mark.asyncio(pytest.mark.django_db(transaction=True)(fn))


async def assert_rejected(token=None):
    """Le serveur accepte puis ferme avec 4401 : le client renouvelle son jeton et se reconnecte."""
    comm = ws(token)
    connected, _ = await comm.connect()
    assert connected
    assert (await comm.receive_output())["code"] == 4401
    await comm.disconnect()


@pytest.fixture
def departed_token(db):
    """Jeton encore valide, mais dont le compte a été supprimé depuis."""
    user = User.objects.create_user("parti@test.tn", "pass-12345", first_name="Parti", last_name="Loin")
    token = token_for(user)
    user.anonymize()
    return token


@websocket_test
async def test_websocket_without_token_is_closed_with_4401():
    await assert_rejected()


@websocket_test
async def test_websocket_with_garbage_token_is_closed_with_4401():
    await assert_rejected("pas-un-jeton")


@websocket_test
async def test_websocket_with_expired_token_is_closed_with_4401(member):
    token = AccessToken.for_user(member)
    token.set_exp(lifetime=-timedelta(seconds=5))
    await assert_rejected(str(token))


@websocket_test
async def test_websocket_with_token_lacking_user_is_closed_with_4401():
    await assert_rejected(str(AccessToken()))


@websocket_test
async def test_websocket_of_deleted_account_is_closed_with_4401(departed_token):
    await assert_rejected(departed_token)


@websocket_test
async def test_websocket_answers_ping_with_pong(member):
    comm = ws(token_for(member))
    connected, _ = await comm.connect()
    assert connected
    await comm.send_json_to({"type": "ping"})
    assert await comm.receive_json_from() == {"event": "pong"}
    await comm.disconnect()


@websocket_test
async def test_websocket_ignores_unknown_client_messages(member):
    comm = ws(token_for(member))
    await comm.connect()
    await comm.send_json_to({"type": "envoyer", "body": "les écritures passent par l'API REST"})
    assert await comm.receive_nothing()
    await comm.disconnect()


@websocket_test
async def test_websocket_receives_events_of_its_own_group_only(member):
    comm = ws(token_for(member))
    await comm.connect()
    await comm.send_json_to({"type": "ping"})
    await comm.receive_json_from()  # connexion établie et abonnée à son groupe
    layer = get_channel_layer()
    payload = {"event": "message.created", "conversation": 1}
    await layer.group_send(f"user_{member.pk + 1000}", {"type": "chat.event", "payload": {"event": "pour-un-autre"}})
    assert await comm.receive_nothing()
    await layer.group_send(f"user_{member.pk}", {"type": "chat.event", "payload": payload})
    assert await comm.receive_json_from() == payload
    await comm.disconnect()


@websocket_test
async def test_websocket_leaves_its_group_on_disconnect(member):
    layer, group = get_channel_layer(), f"user_{member.pk}"
    comm = ws(token_for(member))
    await comm.connect()
    await comm.send_json_to({"type": "ping"})
    await comm.receive_json_from()
    assert layer.groups.get(group)
    await comm.disconnect()
    assert not layer.groups.get(group)


@websocket_test
async def test_message_sent_through_the_api_reaches_the_recipient_socket(member, other):
    comm = ws(token_for(member))
    await comm.connect()
    await comm.send_json_to({"type": "ping"})
    await comm.receive_json_from()
    r = await sync_to_async(start)(client_for(other), member, "Bonjour Olfa")
    assert r.status_code == 201
    event = await comm.receive_json_from()
    assert event["event"] == "message.created" and event["conversation"] == r.data["conversation"]["id"]
    assert event["message"]["body"] == "Bonjour Olfa" and event["message"]["sender"] == other.pk
    await comm.disconnect()