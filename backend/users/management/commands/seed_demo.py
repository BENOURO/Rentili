"""python manage.py seed_demo — crée des comptes de démonstration (supprime les comptes existants)."""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.models import User

PASSWORD = "rentili2026"

MEMBERS = [
    ("karim@rentili.tn", "Karim", "Ben Salah", "Tunis", "+216 22 145 870", "Bricoleur du dimanche et campeur. Je loue mon matériel quand il ne sert pas.", True),
    ("yasmine@rentili.tn", "Yasmine", "Trabelsi", "La Marsa", "+216 98 310 452", "Je préfère louer qu'acheter des objets qui servent deux fois par an.", True),
    ("sami@rentili.tn", "Sami", "Gharbi", "Sfax", "", "Photographe de mariage, je loue une partie de mon matériel.", True),
    ("ines@rentili.tn", "Inès", "Haddad", "Sousse", "+216 55 908 117", "Organisatrice d'événements à Sousse et Monastir.", True),
    ("mehdi@rentili.tn", "Mehdi", "Jlassi", "Ariana", "", "Étudiant, gamer et cycliste.", True),
    ("lina@rentili.tn", "Lina", "Ayari", "Bizerte", "", "", False),
    ("omar@rentili.tn", "Omar", "Chaabane", "Nabeul", "+216 29 774 301", "Jardinier amateur, je prête tondeuse et taille-haie.", True),
    ("salma@rentili.tn", "Salma", "Mejri", "Monastir", "", "Maman de deux enfants, je loue poussette et siège auto.", True),
]


class Command(BaseCommand):
    help = "Crée des comptes de démonstration. Mot de passe : rentili2026"

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(7)
        User.objects.all().delete()
        admin = User.objects.create_superuser("admin@rentili.tn", PASSWORD, first_name="Admin", last_name="RENTILI")
        for email, first, last, city, phone, bio, verified in MEMBERS:
            u = User.objects.create_user(email, PASSWORD, first_name=first, last_name=last, city=city, phone=phone, bio=bio)
            u.date_joined = timezone.now() - timedelta(days=random.randint(20, 400))
            u.save(update_fields=["date_joined"])
        self.stdout.write(self.style.SUCCESS(
            f"{User.objects.count()} comptes créés (dont 1 administrateur). Mot de passe de tous les comptes : {PASSWORD}"
        ))
