from django.urls import path

from .views import avis_collection, avis_detail, avis_eligibles

app_name = "GestionDesAvis"

urlpatterns = [
    path("eligible/", avis_eligibles, name="avis-eligible"),
    path("", avis_collection, name="avis-list"),
    path("<int:pk>/", avis_detail, name="avis-detail"),
]
