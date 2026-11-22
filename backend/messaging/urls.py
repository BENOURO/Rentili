from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.ConversationListCreateView.as_view(), name="conversation_list"),
    path("conversations/<int:pk>/", views.ConversationDetailView.as_view(), name="conversation_detail"),
    path("conversations/<int:pk>/messages/", views.MessageListCreateView.as_view(), name="message_list"),
    path("conversations/<int:pk>/read/", views.MarkReadView.as_view(), name="mark_read"),
    path("messages/<int:pk>/", views.MessageDetailView.as_view(), name="message_detail"),
    path("unread-count/", views.UnreadCountView.as_view(), name="unread_count"),
]