from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Avis
from .serializers import AvisSerializer
from reservations.models import Reservation


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def avis_eligibles(request):
    reviewed_ids = Avis.objects.filter(utilisateur_id=request.user.pk).values_list(
        "reservation_id", flat=True
    )
    eligible = Reservation.objects.filter(
        locataire=request.user,
        statut=Reservation.Statut.TERMINEE,
    ).exclude(pk__in=reviewed_ids).select_related("annonce")

    data = [
        {
            "reservation_id": reservation.pk,
            "annonce_id": reservation.annonce_id,
            "annonce_titre": reservation.annonce.titre,
        }
        for reservation in eligible
    ]
    return Response(data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def avis_collection(request):
    if request.method == "GET":
        return lister_avis(request)
    if not request.user or not request.user.is_authenticated:
        raise PermissionDenied("Authentification requise")
    return creer_avis(request)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def avis_detail(request, pk):
    if request.method == "GET":
        return consulter_avis(request, pk)
    if request.method in ("PUT", "PATCH"):
        return modifier_avis(request, pk)
    return supprimer_avis(request, pk)


def lister_avis(request):
    serializer = AvisSerializer(Avis.objects.all(), many=True)
    return Response(serializer.data)


def creer_avis(request):
    data = request.data.copy()
    data["utilisateur_id"] = request.user.pk
    reservation_id = data.get("reservation_id")
    annonce_id = data.get("annonce_id")
    reservation = Reservation.objects.filter(
        pk=reservation_id,
        locataire=request.user,
        annonce_id=annonce_id,
        statut=Reservation.Statut.TERMINEE,
    ).first()
    if reservation is None:
        raise PermissionDenied(
            "Vous ne pouvez donner un avis que pour une réservation terminée."
        )
    if Avis.objects.filter(
        utilisateur_id=request.user.pk,
        reservation_id=reservation.pk,
    ).exists():
        raise PermissionDenied("Vous avez déjà donné un avis pour cette réservation.")
    serializer = AvisSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def consulter_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    return Response(AvisSerializer(avis).data)


def modifier_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    if avis.utilisateur_id != request.user.pk:
        raise PermissionDenied("Vous ne pouvez modifier que vos propres avis")
    data = request.data.copy()
    data["utilisateur_id"] = avis.utilisateur_id
    serializer = AvisSerializer(
        avis,
        data=data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def supprimer_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    if avis.utilisateur_id != request.user.pk:
        raise PermissionDenied("Vous ne pouvez supprimer que vos propres avis")
    avis.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
