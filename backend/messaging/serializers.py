from rest_framework import serializers

from users.serializers import PublicUserSerializer

from .models import Conversation, Message


class BodySerializer(serializers.Serializer):
    """Texte d'un message (envoi US37, modification US39)."""

    body = serializers.CharField(max_length=2000, error_messages={
        "blank": "Le message ne peut pas être vide.", "required": "Le message ne peut pas être vide.",
        "max_length": "Le message est limité à 2000 caractères."})


class StartConversationSerializer(BodySerializer):
    """Premier message envoyé depuis une annonce."""

    recipient = serializers.IntegerField(min_value=1)
    listing_id = serializers.IntegerField(min_value=1)
    listing_title = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")


class MessageSerializer(serializers.ModelSerializer):
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender", "body", "created_at", "edited_at", "read_at", "is_deleted"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    other = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "listing_id", "listing_title", "other", "last_message", "unread_count", "updated_at"]

    def get_other(self, obj):
        return PublicUserSerializer(obj.other_for(self.context["request"].user), context=self.context).data

    def get_last_message(self, obj):
        last = obj.messages.last()
        return MessageSerializer(last).data if last else None

    def get_unread_count(self, obj):
        if hasattr(obj, "unread"):
            return obj.unread
        user = self.context["request"].user
        return obj.messages.filter(read_at__isnull=True, deleted_at__isnull=True).exclude(sender=user).count()