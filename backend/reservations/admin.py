from django.contrib import admin

from .models import Annonce, Categorie, Photo, Reservation


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ("titre", "proprietaire", "ville", "prix_jour", "caution", "active")
    list_filter = ("active", "categorie")
    search_fields = ("titre", "proprietaire__email")


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "annonce", "ordre", "date_creation")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "annonce", "locataire", "date_debut", "date_fin", "statut", "prix_total")
    list_filter = ("statut",)
    search_fields = ("annonce__titre", "locataire__email")
    date_hierarchy = "date_debut"
