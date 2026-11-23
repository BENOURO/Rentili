from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class Annonce(models.Model):
    proprietaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="annonces")
    titre = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    categorie = models.ForeignKey("Categorie", null=True, blank=True, on_delete=models.SET_NULL, related_name="annonces")
    ville = models.CharField(max_length=80, blank=True)
    prix_jour = models.DecimalField("prix par jour (DT)", max_digits=8, decimal_places=2)
    caution = models.DecimalField("caution (DT)", max_digits=8, decimal_places=2, default=Decimal("0"))
    active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.titre


class Categorie(models.Model):
    nom = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Photo(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="annonces/")
    ordre = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordre", "id"]

    def __str__(self):
        return f"Photo {self.pk} — {self.annonce.titre}"


class Reservation(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        ACCEPTEE = "ACCEPTEE", "Acceptée"
        REFUSEE = "REFUSEE", "Refusée"
        ANNULEE = "ANNULEE", "Annulée"
        TERMINEE = "TERMINEE", "Terminée"

    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name="reservations")
    locataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=12, choices=Statut.choices, default=Statut.EN_ATTENTE, db_index=True)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2)
    caution = models.DecimalField(max_digits=8, decimal_places=2)
    message = models.TextField("message au propriétaire", max_length=1000, blank=True)
    motif_refus = models.CharField(max_length=300, blank=True)
    annulee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_creation"]
        constraints = [
            models.CheckConstraint(condition=Q(date_fin__gte=models.F("date_debut")), name="reservation_dates_ordonnees"),
        ]

    def __str__(self):
        return f"Réservation #{self.pk} · {self.annonce} ({self.get_statut_display()})"

    # --- règles métier -------------------------------------------------------------------------

    @property
    def proprietaire(self):
        return self.annonce.proprietaire

    @staticmethod
    def nombre_jours(debut, fin):
        """Le jour de début et le jour de fin sont tous deux facturés."""
        return (fin - debut).days + 1

    @classmethod
    def calculer_prix(cls, annonce, debut, fin):
        """T21.2 — prix total = nombre de jours × prix par jour (la caution est à part)."""
        return annonce.prix_jour * cls.nombre_jours(debut, fin)

    @classmethod
    def chevauchements(cls, annonce, debut, fin, exclure=None):
        """T21.3 — réservations acceptées de l'annonce dont la période croise [debut, fin]."""
        qs = cls.objects.filter(
            annonce=annonce, statut=cls.Statut.ACCEPTEE, date_debut__lte=fin, date_fin__gte=debut
        )
        if exclure is not None:
            qs = qs.exclude(pk=exclure.pk)
        return qs

    def peut_annuler(self, user):
        """US24 — une demande en attente, ou une réservation acceptée qui n'a pas encore commencé."""
        if user.pk not in (self.locataire_id, self.annonce.proprietaire_id):
            return False
        if self.statut == self.Statut.EN_ATTENTE:
            return True
        return self.statut == self.Statut.ACCEPTEE and self.date_debut > date.today()

    def peut_terminer(self, user):
        """US26 — le propriétaire clôt une location acceptée dont la période a commencé."""
        return (
            user.pk == self.annonce.proprietaire_id
            and self.statut == self.Statut.ACCEPTEE
            and self.date_debut <= date.today()
        )
