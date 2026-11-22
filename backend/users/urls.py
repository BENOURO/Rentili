from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

auth_urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

users_urlpatterns = [
    path("", views.MemberListView.as_view(), name="member_list"),
    path("me/", views.MeView.as_view(), name="me"),
    path("<int:pk>/", views.PublicProfileView.as_view(), name="public_profile"),
]
