from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class PrivateUserSerializer(serializers.ModelSerializer):
    """Profil complet : renvoyé uniquement à l'utilisateur lui-même (US03, US04)."""

    display_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "city", "bio", "avatar",
                  "display_name", "initials", "date_joined", "is_staff"]
        read_only_fields = ["id", "email", "date_joined", "is_staff"]
        extra_kwargs = {"first_name": {"required": True, "allow_blank": False},
                        "last_name": {"required": True, "allow_blank": False}}


class PublicUserSerializer(serializers.ModelSerializer):
    """Profil public (US05) : ni email, ni téléphone, ni nom de famille complet."""

    display_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "display_name", "initials", "city", "bio", "avatar", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Inscription (US01)."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "city"]
        extra_kwargs = {"first_name": {"required": True, "allow_blank": False},
                        "last_name": {"required": True, "allow_blank": False}}

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cette adresse email.")
        return value

    def validate(self, attrs):
        # mêmes règles que Django (longueur, mot de passe courant, trop proche du nom, tout numérique)
        candidate = User(email=attrs["email"], first_name=attrs.get("first_name", ""), last_name=attrs.get("last_name", ""))
        try:
            password_validation.validate_password(attrs["password"], candidate)
        except Exception as exc:  # django.core.exceptions.ValidationError
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, data):
        return User.objects.create_user(**data)


class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    """Connexion (US02) par email + mot de passe ; renvoie les jetons et le profil."""

    default_error_messages = {"no_active_account": "Adresse email ou mot de passe incorrect."}

    def validate(self, attrs):
        attrs[self.username_field] = attrs.get(self.username_field, "").strip().lower()
        data = super().validate(attrs)
        data["user"] = PrivateUserSerializer(self.user, context=self.context).data
        return data
