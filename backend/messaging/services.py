"""Logique métier de la messagerie. Chaque changement est diffusé en temps réel."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from users.models import User

from .models import Conversation, Message
from .serializers import MessageSerializer


def _broadcast(conversation, event, **data):
    """Diffuse l'événement aux deux participants (groupe WebSocket `user_<id>`).

    L'envoi est différé jusqu'à la validation de la transaction en cours (`on_commit`) : on ne diffuse jamais
    un événement pour des données finalement annulées, et un client qui réagit à l'événement en rechargeant
    l'API retrouve déjà le message. Hors transaction, l'envoi part immédiatement."""
    layer = get_channel_layer()
    if layer is None:
        return
    groups = [f"user_{uid}" for uid in (conversation.starter_id, conversation.recipient_id)]
    payload = {"event": event, "conversation": conversation.pk, **data}

    def push():
        send = async_to_sync(layer.group_send)
        for group in groups:
            send(group, {"type": "chat.event", "payload": payload})

    transaction.on_commit(push)


def _ensure_other_is_active(conversation, sender):
    other = conversation.other_for(sender)
    if not other.is_active or other.deleted_at:
        raise PermissionDenied("Ce membre a supprimé son compte : vous ne pouvez plus lui écrire.")


# ---------- US37 : envoi ----------
@transaction.atomic
def start_conversation(sender, recipient_id, listing_id, listing_title, body):
    """Crée la conversation si besoin (une seule par annonce et par paire de membres), puis envoie le message."""
    recipient = User.objects.filter(pk=recipient_id, is_active=True, deleted_at__isnull=True).first()
    if recipient is None:
        raise ValidationError({"recipient": ["Ce membre n'existe pas ou a supprimé son compte."]})
    if recipient.pk == sender.pk:
        raise ValidationError({"recipient": ["Vous ne pouvez pas vous écrire à vous-même."]})
    conversation = (
        Conversation.objects.filter(listing_id=listing_id)
        .filter(Q(starter=sender, recipient=recipient) | Q(starter=recipient, recipient=sender))
        .select_related("starter", "recipient").first()
    )
    if conversation is None:
        conversation = Conversation.objects.create(starter=sender, recipient=recipient, listing_id=listing_id, listing_title=listing_title)
    return conversation, send_message(conversation, sender, body)


def send_message(conversation, sender, body):
    _ensure_other_is_active(conversation, sender)
    message = Message.objects.create(conversation=conversation, sender=sender, body=body)
    Conversation.objects.filter(pk=conversation.pk).update(updated_at=message.created_at)
    _broadcast(conversation, "message.created", message=dict(MessageSerializer(message).data))
    return message


# ---------- US38 : lecture ----------
def mark_read(conversation, user):
    """Marque comme lus les messages reçus par `user`. Renvoie leur nombre."""
    ids = list(conversation.messages.filter(read_at__isnull=True).exclude(sender=user).values_list("id", flat=True))
    if ids:
        now = timezone.now()
        Message.objects.filter(id__in=ids).update(read_at=now)
        _broadcast(conversation, "messages.read", reader=user.pk, message_ids=ids, read_at=now.isoformat())
    return len(ids)


def unread_total(user):
    return (
        Message.objects.filter(Q(conversation__starter=user) | Q(conversation__recipient=user), read_at__isnull=True, deleted_at__isnull=True)
        .exclude(sender=user).count()
    )


# ---------- US39 / US40 : modification et suppression ----------
def edit_message(message, user, body):
    if message.sender_id != user.pk:
        raise PermissionDenied("Vous ne pouvez modifier que vos propres messages.")
    if message.is_deleted:
        raise ValidationError({"detail": ["Ce message a été supprimé."]})
    message.body, message.edited_at = body, timezone.now()
    message.save(update_fields=["body", "edited_at"])
    _broadcast(message.conversation, "message.updated", message=dict(MessageSerializer(message).data))
    return message


def delete_message(message, user):
    if message.sender_id != user.pk:
        raise PermissionDenied("Vous ne pouvez supprimer que vos propres messages.")
    if not message.is_deleted:
        message.body, message.deleted_at = "", timezone.now()
        message.save(update_fields=["body", "deleted_at"])
        _broadcast(message.conversation, "message.deleted", message=dict(MessageSerializer(message).data))
    return message