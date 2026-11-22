from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Avis",
            fields=[
                (
                    "idAvis",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                (
                    "note",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ]
                    ),
                ),
                ("commentaire", models.TextField()),
                ("dateAvis", models.DateTimeField(auto_now_add=True)),
                (
                    "auteurRole",
                    models.CharField(
                        choices=[("LOCATAIRE", "Locataire")],
                        default="LOCATAIRE",
                        max_length=20,
                    ),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("EN_ATTENTE", "En attente"),
                            ("PUBLIE", "Publié"),
                            ("MASQUE", "Masqué"),
                            ("SUPPRIME", "Supprimé"),
                        ],
                        default="EN_ATTENTE",
                        max_length=20,
                    ),
                ),
                (
                    "sentiment",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("POSITIF", "Positif"),
                            ("NEUTRE", "Neutre"),
                            ("NEGATIF", "Négatif"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "scoreFraude",
                    models.FloatField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0.0),
                            django.core.validators.MaxValueValidator(1.0),
                        ],
                    ),
                ),
                ("utilisateur_id", models.PositiveBigIntegerField()),
                ("annonce_id", models.PositiveBigIntegerField()),
                ("reservation_id", models.PositiveBigIntegerField()),
            ],
            options={
                "db_table": "avis",
                "ordering": ["-dateAvis"],
            },
        ),
        migrations.AddConstraint(
            model_name="avis",
            constraint=models.UniqueConstraint(
                fields=("utilisateur_id", "reservation_id"),
                name="unique_avis_par_locataire_reservation",
            ),
        ),
    ]
