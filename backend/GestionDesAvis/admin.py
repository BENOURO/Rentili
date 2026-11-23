from django.contrib import admin

from .models import Avis


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = (
        "idAvis",
        "note",
        "statut",
        "sentiment",
        "dateAvis",
        "annonce_id",
        "utilisateur_id",
    )
    list_filter = ("statut", "sentiment", "note")
    search_fields = ("commentaire",)

