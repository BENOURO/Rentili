from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Avis
from .serializers import AvisSerializer


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def avis_collection(request):
    if request.method == "GET":
        return lister_avis(request)
    return creer_avis(request)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
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
    serializer = AvisSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def consulter_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    return Response(AvisSerializer(avis).data)


def modifier_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    serializer = AvisSerializer(
        avis,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def supprimer_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    avis.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
