from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reservations"
    verbose_name = "Gestion des réservations"

    def ready(self):
        from . import receivers  # noqa: F401  (abonnement au signal user_deleted)
