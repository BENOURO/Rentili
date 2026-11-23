"""Routes du backend RENTILI. Chaque module ajoute ses routes sous /api/."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from users.urls import auth_urlpatterns, users_urlpatterns

admin.site.site_header = "RENTILI — Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    # Module « Gestion des utilisateurs »
    path('api/auth/', include(auth_urlpatterns)),
    path('api/users/', include(users_urlpatterns)),
    path('api/messaging/', include('messaging.urls')),
    path('api/avis/', include('GestionDesAvis.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

