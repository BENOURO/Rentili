from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Une connexion par utilisateur : elle reçoit tous les événements de ses conversations.
    Les écritures passent par l'API REST ; le WebSocket ne sert qu'à diffuser."""

    async def connect(self):
        user = self.scope.get("user")
        await self.accept()
        if user is None or user.is_anonymous:
            await self.close(code=4401)  # jeton absent ou expiré : le client le renouvelle et se reconnecte
            return
        self.group = f"user_{user.pk}"
        await self.channel_layer.group_add(self.group, self.channel_name)

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"event": "pong"})

    async def chat_event(self, event):
        await self.send_json(event["payload"])