"""Router for users api."""
from django.urls import path

from users import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view({'post': 'create'}), name='register'),
    path("auth/login/", )
]
