from rest_framework import serializers

from .models import Avis
from reservations.models import Annonce, Reservation
from users.models import User


class AvisSerializer(serializers.ModelSerializer):
    idAvis = serializers.IntegerField(source="pk", read_only=True)
    dateAvis = serializers.DateTimeField(read_only=True)
    auteurRole = serializers.CharField(read_only=True)
    statut = serializers.CharField(read_only=True)
    sentiment = serializers.CharField(read_only=True)
    scoreFraude = serializers.FloatField(read_only=True)
    locataire_name = serializers.SerializerMethodField()
    annonce_titre = serializers.SerializerMethodField()
    proprietaire_name = serializers.SerializerMethodField()

    def get_locataire_name(self, avis):
        reservation = Reservation.objects.filter(pk=avis.reservation_id).first()
        if reservation:
            user = reservation.locataire
            return user.display_name
        user = User.objects.filter(pk=avis.utilisateur_id).first()
        if not user:
            return f"Utilisateur {avis.utilisateur_id}"
        return user.display_name

    def get_annonce_titre(self, avis):
        annonce = Annonce.objects.filter(pk=avis.annonce_id).first()
        return annonce.titre if annonce else f"Annonce {avis.annonce_id}"

    def get_proprietaire_name(self, avis):
        annonce = Annonce.objects.select_related("proprietaire").filter(pk=avis.annonce_id).first()
        if annonce:
            return annonce.proprietaire.display_name
        return f"Propriétaire {avis.annonce_id}"

    class Meta:
        model = Avis
        fields = [
            "idAvis",
            "utilisateur_id",
            "annonce_id",
            "reservation_id",
            "note",
            "commentaire",
            "dateAvis",
            "auteurRole",
            "statut",
            "sentiment",
            "scoreFraude",
            "locataire_name",
            "annonce_titre",
            "proprietaire_name",
        ]
