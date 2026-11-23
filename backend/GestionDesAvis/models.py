from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AuteurRole(models.TextChoices):
    LOCATAIRE = "LOCATAIRE", "Locataire"


class StatutAvis(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    PUBLIE = "PUBLIE", "Publié"
    MASQUE = "MASQUE", "Masqué"
    SUPPRIME = "SUPPRIME", "Supprimé"


class Sentiment(models.TextChoices):
    POSITIF = "POSITIF", "Positif"
    NEUTRE = "NEUTRE", "Neutre"
    NEGATIF = "NEGATIF", "Négatif"


class Avis(models.Model):
    idAvis = models.BigAutoField(primary_key=True)
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    commentaire = models.TextField()
    dateAvis = models.DateTimeField(auto_now_add=True)
    auteurRole = models.CharField(
        max_length=20,
        choices=AuteurRole.choices,
        default=AuteurRole.LOCATAIRE,
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutAvis.choices,
        default=StatutAvis.EN_ATTENTE,
    )
    sentiment = models.CharField(
        max_length=20,
        choices=Sentiment.choices,
        blank=True,
    )
    scoreFraude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    utilisateur_id = models.PositiveBigIntegerField()
    annonce_id = models.PositiveBigIntegerField()
    reservation_id = models.PositiveBigIntegerField()

    class Meta:
        db_table = "avis"
        ordering = ["-dateAvis"]
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur_id", "reservation_id"],
                name="unique_avis_par_locataire_reservation",
            )
        ]

    def __str__(self):
        return f"Avis {self.idAvis} - note {self.note}/5"

