from django.urls import path

from . import views

urlpatterns = [
    path("", views.ReservationListCreateView.as_view(), name="reservation_list"),
    path("<int:pk>/", views.ReservationDetailView.as_view(), name="reservation_detail"),
    path("<int:pk>/accepter/", views.AccepterView.as_view(), name="reservation_accepter"),
    path("<int:pk>/refuser/", views.RefuserView.as_view(), name="reservation_refuser"),
    path("<int:pk>/annuler/", views.AnnulerView.as_view(), name="reservation_annuler"),
    path("<int:pk>/terminer/", views.TerminerView.as_view(), name="reservation_terminer"),
    # Annonces minimales (lecture seule) en attendant le module « Gestion des annonces »
    path("annonces/", views.AnnonceListView.as_view(), name="annonce_list"),
    path("annonces/<int:pk>/", views.AnnonceDetailView.as_view(), name="annonce_detail"),
]
