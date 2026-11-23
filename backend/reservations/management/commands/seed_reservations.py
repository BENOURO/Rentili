"""python manage.py seed_reservations — annonces et réservations de démonstration.

À lancer après `python manage.py seed_demo` (il faut les comptes de démonstration).
Les annonces et réservations existantes sont supprimées.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from reservations.models import Annonce, Reservation
from users.models import User

ANNONCES = [
    # propriétaire, titre, catégorie, ville, prix/jour, caution, description
    ("karim@rentili.tn", "Perceuse-visseuse Bosch 18V", "Bricolage", "Tunis", "15", "100", "Deux batteries, coffret d'embouts inclus."),
    ("karim@rentili.tn", "Tente familiale 4 places", "Camping", "Tunis", "25", "150", "Montage en 10 minutes, tapis de sol fourni."),
    ("sami@rentili.tn", "Canon EOS 2000D + objectif 18-55", "Photo", "Sfax", "40", "400", "Carte SD 64 Go et sacoche fournies."),
    ("ines@rentili.tn", "Sono portable 300W", "Événementiel", "Sousse", "60", "300", "Deux micros sans fil, autonomie 8 h."),
    ("omar@rentili.tn", "Tondeuse électrique", "Jardin", "Nabeul", "20", "120", "Bac de ramassage 40 L."),
    ("salma@rentili.tn", "Poussette tout-terrain", "Puériculture", "Monastir", "10", "80", "Pliable d'une main, habillage pluie inclus."),
]

J = lambda n: date.today() + timedelta(days=n)  # noqa: E731
S = Reservation.Statut

RESERVATIONS = [
    # annonce (index), locataire, début, fin, statut, message / motif
    (0, "yasmine@rentili.tn", 3, 5, S.EN_ATTENTE, "Bonjour, pour monter des étagères ce week-end."),
    (1, "mehdi@rentili.tn", 10, 13, S.EN_ATTENTE, "Sortie camping à Ain Draham."),
    (1, "yasmine@rentili.tn", 20, 22, S.ACCEPTEE, ""),
    (2, "karim@rentili.tn", 6, 7, S.EN_ATTENTE, "Pour un anniversaire."),
    (3, "karim@rentili.tn", -6, -4, S.TERMINEE, "Soirée de fiançailles."),
    (4, "karim@rentili.tn", -2, 1, S.ACCEPTEE, ""),
    (5, "karim@rentili.tn", 15, 16, S.REFUSEE, "Déjà prêtée à ma sœur ces jours-là."),
    (0, "mehdi@rentili.tn", -10, -8, S.TERMINEE, ""),
    (0, "ines@rentili.tn", -1, 1, S.ACCEPTEE, "Pour accrocher des cadres au salon."),
]


class Command(BaseCommand):
    help = "Crée des annonces et des réservations de démonstration (après seed_demo)."

    @transaction.atomic
    def handle(self, *args, **opts):
        emails = {e for e, *_ in ANNONCES} | {r[1] for r in RESERVATIONS}
        users = {u.email: u for u in User.objects.filter(email__in=emails)}
        if len(users) < len(emails):
            raise CommandError("Comptes de démonstration introuvables : lancez d'abord `python manage.py seed_demo`.")

        Reservation.objects.all().delete()
        Annonce.objects.all().delete()
        annonces = [
            Annonce.objects.create(
                proprietaire=users[email], titre=titre, categorie=cat, ville=ville,
                prix_jour=Decimal(prix), caution=Decimal(caution), description=desc,
            )
            for email, titre, cat, ville, prix, caution, desc in ANNONCES
        ]
        for i, email, debut, fin, statut, texte in RESERVATIONS:
            a = annonces[i]
            Reservation.objects.create(
                annonce=a, locataire=users[email], date_debut=J(debut), date_fin=J(fin), statut=statut,
                prix_total=Reservation.calculer_prix(a, J(debut), J(fin)), caution=a.caution,
                message="" if statut == S.REFUSEE else texte,
                motif_refus=texte if statut == S.REFUSEE else "",
            )
        self.stdout.write(self.style.SUCCESS(
            f"{len(annonces)} annonces et {len(RESERVATIONS)} réservations créées. "
            "Connectez-vous avec karim@rentili.tn (rentili2026) : il est propriétaire et locataire."
        ))
