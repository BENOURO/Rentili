"""API REST du module « Gestion des utilisateurs » — Sprint 1 (US01 à US06)."""

from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import EmailTokenObtainSerializer, PrivateUserSerializer, PublicUserSerializer, RegisterSerializer
from .signals import user_deleted


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegisterView(generics.CreateAPIView):
    """US01 — POST /api/auth/register/ : crée le compte (Create) et connecte directement l'utilisateur."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        body = {**tokens_for(user), "user": PrivateUserSerializer(user, context={"request": request}).data}
        return Response(body, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """US02 — POST /api/auth/login/ {email, password} → {access, refresh, user}.
    La déconnexion se fait côté client : le front supprime ses jetons."""

    serializer_class = EmailTokenObtainSerializer


class MeView(generics.RetrieveUpdateDestroyAPIView):
    """Mon profil — US03 GET (Read), US04 PATCH (Update), US06 DELETE (Delete) — /api/users/me/"""

    serializer_class = PrivateUserSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # multipart pour la photo de profil

    def get_object(self):
        return self.request.user

    def perform_destroy(self, user):
        user_deleted.send(sender=User, user=user)  # les autres modules réagissent (annonces, réservations)
        user.anonymize()


def active_members():
    return User.objects.filter(is_active=True, deleted_at__isnull=True, is_staff=False).order_by("-date_joined")


class MemberListView(generics.ListAPIView):
    """GET /api/users/ — liste des membres (Read), point d'accès aux profils publics."""

    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return active_members()


class PublicProfileView(generics.RetrieveAPIView):
    """US05 — GET /api/users/<id>/ : profil public d'un membre (Read)."""

    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
    queryset = active_members()
