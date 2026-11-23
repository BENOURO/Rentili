"""API REST de la messagerie (US37 à US40)."""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Conversation, Message
from .serializers import BodySerializer, ConversationSerializer, MessageSerializer, StartConversationSerializer

PAGE = 50


class InboxPagination(PageNumberPagination):
    page_size = 50


def user_conversations(user):
    return Conversation.objects.filter(Q(starter=user) | Q(recipient=user)).select_related("starter", "recipient")


class ConversationListCreateView(generics.ListCreateAPIView):
    """GET /api/messaging/conversations/ — boîte de réception.
    POST — US37 : envoie un message à propos d'une annonce (crée la conversation si besoin)."""

    serializer_class = ConversationSerializer
    pagination_class = InboxPagination

    def get_queryset(self):
        user = self.request.user
        unread = Count("messages", filter=Q(messages__read_at__isnull=True, messages__deleted_at__isnull=True) & ~Q(messages__sender_id=user.pk))
        return user_conversations(user).annotate(unread=unread).order_by("-updated_at", "-pk")
    def create(self, request, *args, **kwargs):
        data = StartConversationSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        v = data.validated_data
        conversation, message = services.start_conversation(request.user, v["recipient"], v["listing_id"], v["listing_title"], v["body"])
        return Response({"conversation": ConversationSerializer(conversation, context=self.get_serializer_context()).data,
                         "message": MessageSerializer(message).data}, status=status.HTTP_201_CREATED)


class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return user_conversations(self.request.user)


class MessageListCreateView(APIView):
    """GET (US38) : les 50 derniers messages, ordre chronologique ; `?before=<id>` pour remonter.
    POST (US37) : envoie un message dans la conversation."""

    def get(self, request, pk):
        conversation = get_object_or_404(user_conversations(request.user), pk=pk)
        qs = conversation.messages.all()
        before = request.query_params.get("before", "")
        if before.isdigit():
            qs = qs.filter(pk__lt=int(before))
        rows = list(qs.order_by("-created_at", "-pk")[: PAGE + 1])
        return Response({"results": MessageSerializer(rows[:PAGE][::-1], many=True).data, "has_more": len(rows) > PAGE})

    def post(self, request, pk):
        conversation = get_object_or_404(user_conversations(request.user), pk=pk)
        data = BodySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        message = services.send_message(conversation, request.user, data.validated_data["body"])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MarkReadView(APIView):
    """POST /api/messaging/conversations/<id>/read/ — T38.3."""

    def post(self, request, pk):
        conversation = get_object_or_404(user_conversations(request.user), pk=pk)
        return Response({"marked": services.mark_read(conversation, request.user)})


class MessageDetailView(APIView):
    """PATCH (US39) modifier, DELETE (US40) supprimer — réservé à l'auteur du message."""

    def _message(self, request, pk):
        qs = Message.objects.select_related("conversation").filter(Q(conversation__starter=request.user) | Q(conversation__recipient=request.user))
        return get_object_or_404(qs, pk=pk)

    def patch(self, request, pk):
        data = BodySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        message = services.edit_message(self._message(request, pk), request.user, data.validated_data["body"])
        return Response(MessageSerializer(message).data)

    def delete(self, request, pk):
        services.delete_message(self._message(request, pk), request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnreadCountView(APIView):
    """GET /api/messaging/unread-count/ — pastille de la barre de navigation."""

    def get(self, request):
        return Response({"count": services.unread_total(request.user)})