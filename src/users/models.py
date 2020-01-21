"""DB tables for users."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class User(AbstractUser, BaseModel):
    """Chiliseed user object."""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username",)

    email = models.EmailField(
        _("email address"), blank=False, null=False, unique=True
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
    )
