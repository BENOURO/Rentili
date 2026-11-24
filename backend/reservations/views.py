from datetime import date

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Annonce, Categorie, Photo, Reservation
from .serializers import (
    AnnonceDetailSerializer, AnnonceSerializer, CategorieSerializer,
    RefusSerializer, ReservationSerializer,
)

S = Reservation.Statut


# --- Annonces (gestion complète) --------------------------------------------------------------

class CategorieListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    pagination_class = None


class AnnonceListCreateView(generics.ListCreateAPIView):
    serializer_class = AnnonceSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()] if self.request.method == "POST" else [permissions.AllowAny()]

    def get_queryset(self):
        params = self.request.query_params
        if params.get("mine") == "true" and self.request.user.is_authenticated:
            qs = Annonce.objects.filter(proprietaire=self.request.user, active=True)
        else:
            qs = Annonce.objects.filter(active=True)
        qs = qs.select_related("proprietaire", "categorie").prefetch_related("photos")
        recherche = params.get("search") or params.get("q")
        if recherche:
            qs = qs.filter(Q(titre__icontains=recherche) | Q(description__icontains=recherche))
        categorie = params.get("categorie")
        if categorie:
            if categorie.isdigit():
                qs = qs.filter(categorie_id=int(categorie))
            else:
                qs = qs.filter(categorie__nom__iexact=categorie)
        ville = params.get("ville")
        if ville:
            qs = qs.filter(ville__icontains=ville)
        prix_min = params.get("prix_min")
        prix_max = params.get("prix_max")
        if prix_min:
            qs = qs.filter(prix_jour__gte=prix_min)
        if prix_max:
            qs = qs.filter(prix_jour__lte=prix_max)
        debut, fin = params.get("date_debut"), params.get("date_fin")
        if debut and fin:
            qs = qs.exclude(
                reservations__statut=Reservation.Statut.ACCEPTEE,
                reservations__date_debut__lte=fin,
                reservations__date_fin__gte=debut,
            ).distinct()
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        annonce = serializer.save()
        for ordre, image in enumerate(request.FILES.getlist("photos")):
            Photo.objects.create(annonce=annonce, image=image, ordre=ordre)
        data = AnnonceDetailSerializer(annonce, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class AnnonceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AnnonceDetailSerializer

    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method in ("GET", "HEAD", "OPTIONS") else [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Annonce.objects.select_related("proprietaire", "categorie").prefetch_related("photos")
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return qs.filter(proprietaire=self.request.user)
        return qs.filter(active=True)

    def update(self, request, *args, **kwargs):
        annonce = self.get_object()
        if annonce.proprietaire_id != request.user.pk:
            raise PermissionDenied("Seul le propriétaire peut modifier cette annonce.")
        response = super().update(request, *args, partial=kwargs.pop("partial", True))
        photos = request.FILES.getlist("photos")
        if photos:
            annonce.photos.all().delete()
            for ordre, image in enumerate(photos):
                Photo.objects.create(annonce=annonce, image=image, ordre=ordre)
        annonce.refresh_from_db()
        return Response(AnnonceDetailSerializer(annonce, context={"request": request}).data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Archive the announcement and cancel reservations that have not started."""
        annonce = self.get_object()
        if annonce.proprietaire_id != request.user.pk:
            raise PermissionDenied("Seul le propriétaire peut supprimer cette annonce.")
        annonce.active = False
        annonce.save(update_fields=["active", "date_modification"])
        annonce.reservations.filter(
            Q(statut=S.EN_ATTENTE) | Q(statut=S.ACCEPTEE, date_debut__gt=date.today())
        ).update(statut=S.ANNULEE, annulee_par=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        if not r.annonce.active:
            raise ValidationError({"detail": "Cette annonce a été retirée."})
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
