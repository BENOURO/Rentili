from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True)
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Utilisateur de la plateforme. Locataire et propriétaire sont des rôles, pas des comptes distincts."""

    username = None
    email = models.EmailField("email", unique=True)
    phone = models.CharField("téléphone", max_length=20, blank=True)
    city = models.CharField("ville", max_length=80, blank=True)
    bio = models.TextField("présentation", max_length=500, blank=True)
    avatar = models.ImageField("photo de profil", upload_to="avatars/", blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        verbose_name = "utilisateur"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        name = f"{self.first_name} {self.last_name[:1]}.".strip() if self.last_name else self.first_name
        return name or self.email.split("@")[0]

    @property
    def initials(self):
        return ((self.first_name[:1] + self.last_name[:1]) or self.email[:2]).upper()

    def anonymize(self):
        """Suppression du compte : données personnelles effacées, historique (réservations, avis) conservé."""
        self.first_name, self.last_name = "Utilisateur", "supprimé"
        self.email = f"supprime-{self.pk}@rentili.invalid"
        self.phone = self.city = self.bio = ""
        self.avatar = None
        self.is_active = False
        self.deleted_at = timezone.now()
        self.set_unusable_password()
        self.save()
