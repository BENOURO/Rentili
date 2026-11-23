from datetime import date, timedelta

from rest_framework import serializers

from .models import Annonce, Reservation

DUREE_MAX = 90  # jours


class MembreSerializer(serializers.Serializer):
    """Identité publique d'un membre (jamais l'email ni le téléphone)."""

    id = serializers.IntegerField()
    display_name = serializers.CharField()
    initials = serializers.CharField()
    city = serializers.CharField()


class AnnonceSerializer(serializers.ModelSerializer):
    proprietaire = MembreSerializer(read_only=True)

    class Meta:
        model = Annonce
        fields = ["id", "titre", "description", "categorie", "ville", "prix_jour", "caution", "proprietaire"]


class AnnonceDetailSerializer(AnnonceSerializer):
    periodes_reservees = serializers.SerializerMethodField()

    class Meta(AnnonceSerializer.Meta):
        fields = AnnonceSerializer.Meta.fields + ["periodes_reservees"]

    def get_periodes_reservees(self, annonce):
        """Périodes déjà acceptées, pour que le locataire choisisse des dates libres."""
        qs = annonce.reservations.filter(statut=Reservation.Statut.ACCEPTEE, date_fin__gte=date.today())
        return [{"date_debut": r.date_debut, "date_fin": r.date_fin} for r in qs.order_by("date_debut")]


class ReservationSerializer(serializers.ModelSerializer):
    annonce = AnnonceSerializer(read_only=True)
    locataire = MembreSerializer(read_only=True)
    annonce_id = serializers.PrimaryKeyRelatedField(
        source="annonce", queryset=Annonce.objects.filter(active=True), write_only=True
    )
    statut_label = serializers.CharField(source="get_statut_display", read_only=True)
    nb_jours = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            "id", "annonce", "annonce_id", "locataire", "date_debut", "date_fin", "nb_jours",
            "statut", "statut_label", "prix_total", "caution", "message", "motif_refus",
            "role", "actions", "date_creation",
        ]
        read_only_fields = ["statut", "prix_total", "caution", "motif_refus", "date_creation"]

    def get_nb_jours(self, r):
        return Reservation.nombre_jours(r.date_debut, r.date_fin)

    def _user(self):
        return self.context["request"].user

    def get_role(self, r):
        return "proprietaire" if r.annonce.proprietaire_id == self._user().pk else "locataire"

    def get_actions(self, r):
        """Ce que l'utilisateur connecté peut faire sur cette réservation (le front affiche les boutons en conséquence)."""
        user = self._user()
        est_proprio = r.annonce.proprietaire_id == user.pk
        en_attente = r.statut == Reservation.Statut.EN_ATTENTE
        return {
            "accepter": est_proprio and en_attente,
            "refuser": est_proprio and en_attente,
            "modifier": r.locataire_id == user.pk and en_attente,
            "annuler": r.peut_annuler(user),
            "terminer": r.peut_terminer(user),
        }

    # --- validation -----------------------------------------------------------------------------

    def validate(self, data):
        annonce = data.get("annonce") or self.instance.annonce
        debut = data.get("date_debut", getattr(self.instance, "date_debut", None))
        fin = data.get("date_fin", getattr(self.instance, "date_fin", None))
        user = self._user()

        if self.instance is None and annonce.proprietaire_id == user.pk:
            raise serializers.ValidationError({"annonce_id": ["Vous ne pouvez pas réserver votre propre objet."]})
        if debut < date.today():
            raise serializers.ValidationError({"date_debut": ["La date de début ne peut pas être dans le passé."]})
        if fin < debut:
            raise serializers.ValidationError({"date_fin": ["La date de fin doit être après la date de début."]})
        if fin - debut >= timedelta(days=DUREE_MAX):
            raise serializers.ValidationError({"date_fin": [f"Une location ne peut pas dépasser {DUREE_MAX} jours."]})
        if Reservation.chevauchements(annonce, debut, fin, exclure=self.instance).exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["L'objet est déjà réservé sur une partie de cette période."]}
            )
        doublon = Reservation.objects.filter(
            annonce=annonce, locataire=user, statut=Reservation.Statut.EN_ATTENTE,
            date_debut__lte=fin, date_fin__gte=debut,
        )
        if self.instance is not None:
            doublon = doublon.exclude(pk=self.instance.pk)
        if doublon.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["Vous avez déjà une demande en attente pour cet objet sur ces dates."]}
            )
        return data

    def create(self, data):
        annonce = data["annonce"]
        return Reservation.objects.create(
            **data,
            locataire=self._user(),
            prix_total=Reservation.calculer_prix(annonce, data["date_debut"], data["date_fin"]),
            caution=annonce.caution,
        )

    def update(self, r, data):
        """US25 — seules les dates et le message changent ; le prix est recalculé."""
        data.pop("annonce", None)
        for field, value in data.items():
            setattr(r, field, value)
        r.prix_total = Reservation.calculer_prix(r.annonce, r.date_debut, r.date_fin)
        r.save()
        return r


class RefusSerializer(serializers.Serializer):
    motif = serializers.CharField(max_length=300, required=False, allow_blank=True)
