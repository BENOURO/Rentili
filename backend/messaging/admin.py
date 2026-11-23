from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "listing_id", "listing_title", "starter", "recipient", "updated_at"]
    search_fields = ["listing_title", "starter__email", "recipient__email"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender", "created_at", "read_at", "deleted_at"]
    list_filter = ["deleted_at"]