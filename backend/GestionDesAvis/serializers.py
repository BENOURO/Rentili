from rest_framework import serializers

from .models import Avis


class AvisSerializer(serializers.ModelSerializer):
    idAvis = serializers.IntegerField(source="pk", read_only=True)
    dateAvis = serializers.DateTimeField(read_only=True)
    auteurRole = serializers.CharField(read_only=True)
    statut = serializers.CharField(read_only=True)
    sentiment = serializers.CharField(read_only=True)
    scoreFraude = serializers.FloatField(read_only=True)

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
        ]
