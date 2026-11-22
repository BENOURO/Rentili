from django.urls import path

from .views import avis_collection, avis_detail

app_name = "GestionDesAvis"

urlpatterns = [
    path("", avis_collection, name="avis-list"),
    path("<int:pk>/", avis_detail, name="avis-detail"),
]
