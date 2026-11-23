from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Annonce, Reservation
from .serializers import AnnonceDetailSerializer, AnnonceSerializer, RefusSerializer, ReservationSerializer

S = Reservation.Statut


# --- Annonces (lecture seule, en attendant le module Annonces) ---------------------------------

class AnnonceListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AnnonceSerializer
    queryset = Annonce.objects.filter(active=True).select_related("proprietaire")


class AnnonceDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AnnonceDetailSerializer
    queryset = Annonce.objects.filter(active=True).select_related("proprietaire")


# --- Réservations ------------------------------------------------------------------------------

def mes_reservations(user):
    return Reservation.objects.filter(Q(locataire=user) | Q(annonce__proprietaire=user)).select_related(
        "annonce", "annonce__proprietaire", "locataire"
    )


class ReservationListCreateView(generics.ListCreateAPIView):
    """GET : US23 — mes réservations (?role=locataire|proprietaire, ?statut=…). POST : US21 — demander."""

    serializer_class = ReservationSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        qs = mes_reservations(user)
        role = self.request.query_params.get("role")
        if role == "locataire":
            qs = qs.filter(locataire=user)
        elif role == "proprietaire":
            qs = qs.filter(annonce__proprietaire=user)
        statut = self.request.query_params.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        return qs


class ReservationDetailView(generics.RetrieveUpdateAPIView):
    """GET : détail (participants seulement). PATCH : US25 — le locataire modifie les dates d'une demande en attente."""

    serializer_class = ReservationSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return mes_reservations(self.request.user)

    def update(self, request, *args, **kwargs):
        r = self.get_object()
        if r.locataire_id != request.user.pk:
            raise PermissionDenied("Seul le locataire peut modifier sa demande.")
        if r.statut != S.EN_ATTENTE:
            raise ValidationError({"detail": "Seule une demande en attente peut être modifiée."})
        return super().update(request, *args, partial=True)


class ReservationActionView(APIView):
    """Base des actions de changement de statut : POST /api/reservations/<id>/<action>/."""

    def get_reservation(self, pk):
        return get_object_or_404(mes_reservations(self.request.user).select_for_update(), pk=pk)

    def reponse(self, r):
        return Response(ReservationSerializer(r, context={"request": self.request}).data)


class AccepterView(ReservationActionView):
    """US22 — le propriétaire accepte. Les autres demandes qui chevauchent la période sont refusées automatiquement."""

    @transaction.atomic
    def post(self, request, pk):
        r = self.get_reservation(pk)
        if r.annonce.proprietaire_id != request.user.pk:
            raise PermissionDenied("Seul le propriétaire peut accepter une demande.")
        if r.statut != S.EN_ATTENTE:
            raise ValidationError({"detail": "Cette demande n'est plus en attente."})
        if Reservation.chevauchements(r.annonce, r.date_debut, r.date_fin, exclure=r).exists():
            raise ValidationError({"detail": "L'objet est déjà réservé sur une partie de cette période."})
        r.statut = S.ACCEPTEE
        r.save(update_fields=["statut", "date_modification"])
        Reservation.objects.filter(
            annonce=r.annonce, statut=S.EN_ATTENTE, date_debut__lte=r.date_fin, date_fin__gte=r.date_debut
        ).exclude(pk=r.pk).update(statut=S.REFUSEE, motif_refus="L'objet a été réservé par un autre membre sur ces dates.")
        return self.reponse(r)


class RefuserView(ReservationActionView):
    """US22 — le propriétaire refuse, avec un motif facultatif."""

    @transaction.atomic
    def post(self, request, pk):
        r = self.get_reservation(pk)
        if r.annonce.proprietaire_id != request.user.pk:
            raise PermissionDenied("Seul le propriétaire peut refuser une demande.")
        if r.statut != S.EN_ATTENTE:
            raise ValidationError({"detail": "Cette demande n'est plus en attente."})
        s = RefusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        r.statut, r.motif_refus = S.REFUSEE, s.validated_data.get("motif", "")
        r.save(update_fields=["statut", "motif_refus", "date_modification"])
        return self.reponse(r)


class AnnulerView(ReservationActionView):
    """US24 — locataire ou propriétaire annule une demande en attente ou une réservation pas encore commencée."""

    @transaction.atomic
    def post(self, request, pk):
        r = self.get_reservation(pk)
        if not r.peut_annuler(request.user):
            raise ValidationError({"detail": "Cette réservation ne peut plus être annulée."})
        r.statut, r.annulee_par = S.ANNULEE, request.user
        r.save(update_fields=["statut", "annulee_par", "date_modification"])
        return self.reponse(r)


class TerminerView(ReservationActionView):
    """US26 — le propriétaire marque la location comme terminée (le locataire peut alors laisser un avis)."""

    @transaction.atomic
    def post(self, request, pk):
        r = self.get_reservation(pk)
        if r.annonce.proprietaire_id != request.user.pk:
            raise PermissionDenied("Seul le propriétaire peut terminer une location.")
        if not r.peut_terminer(request.user):
            raise ValidationError({"detail": "Seule une location acceptée et commencée peut être terminée."})
        r.statut = S.TERMINEE
        r.save(update_fields=["statut", "date_modification"])
        return self.reponse(r)
