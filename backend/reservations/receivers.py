from django.db.models import Q
from django.dispatch import receiver

from users.signals import user_deleted

from .models import Reservation


@receiver(user_deleted)
def annuler_reservations(sender, user, **kwargs):
    """Compte supprimé : ses demandes en attente et ses réservations à venir sont annulées,
    qu'il soit locataire ou propriétaire. L'historique (terminées, refusées) est conservé."""
    from datetime import date

    actives = Reservation.objects.filter(Q(locataire=user) | Q(annonce__proprietaire=user))
    actives.filter(statut=Reservation.Statut.EN_ATTENTE).update(
        statut=Reservation.Statut.ANNULEE, annulee_par=user
    )
    actives.filter(statut=Reservation.Statut.ACCEPTEE, date_debut__gt=date.today()).update(
        statut=Reservation.Statut.ANNULEE, annulee_par=user
    )
    user.annonces.update(active=False)
