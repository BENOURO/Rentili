from django import forms

from .models import Avis


class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = [
            "utilisateur_id",
            "annonce_id",
            "reservation_id",
            "note",
            "commentaire",
        ]
        labels = {
            "utilisateur_id": "Utilisateur",
            "annonce_id": "Annonce",
            "reservation_id": "Réservation",
            "note": "Note",
            "commentaire": "Commentaire",
        }
