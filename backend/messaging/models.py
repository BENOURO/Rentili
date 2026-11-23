from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Conversation(models.Model):
    """Échange entre deux membres à propos d'une annonce (US37).

    L'annonce est référencée par son identifiant pour que ce module reste indépendant du module Annonces.
    Quand `Listing` existera, remplacer `listing_id` par une ForeignKey.
    """

    starter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="started_conversations")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_conversations")
    listing_id = models.PositiveIntegerField("annonce")
    listing_title = models.CharField("titre de l'annonce", max_length=160, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["listing_id", "starter", "recipient"], name="uniq_conversation_per_listing_pair"),
            models.CheckConstraint(condition=~Q(starter=F("recipient")), name="conversation_not_with_self"),
        ]

    def __str__(self):
        return f"#{self.pk} · annonce {self.listing_id}"

    def has_participant(self, user):
        return user.pk in (self.starter_id, self.recipient_id)

    def other_for(self, user):
        return self.recipient if user.pk == self.starter_id else self.starter


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)   # US39
    deleted_at = models.DateTimeField(null=True, blank=True)  # US40 : suppression logique, le texte est effacé
    read_at = models.DateTimeField(null=True, blank=True)     # US38 : lu par le destinataire

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"Message {self.pk} de {self.sender_id}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None