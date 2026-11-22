from django.dispatch import Signal

# Envoyé juste avant l'anonymisation d'un compte supprimé (US06), avec l'argument `user`.
# Les autres modules s'y abonnent sans que ce module ait besoin de les connaître, par exemple :
#   annonces     → archiver les annonces de l'utilisateur
#   réservations → annuler ses demandes en attente ou acceptées
#
#   from django.dispatch import receiver
#   from users.signals import user_deleted
#
#   @receiver(user_deleted)
#   def archive_listings(sender, user, **kwargs):
#       Listing.objects.filter(owner=user).update(status=Listing.Status.ARCHIVED)
user_deleted = Signal()
