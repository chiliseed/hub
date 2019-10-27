"""Router for users api."""
from django.urls import path

from users import views

app_name = "users"
urlpatterns = [
    path(
        "auth/register/",
        views.RegisterView.as_view({"post": "create"}),
        name="register",
    ),
    path("auth/login/", views.TokenCreateView.as_view(), name="login"),
    path("auth/logout/", views.TokenDestroyView.as_view(), name="logout"),
]
