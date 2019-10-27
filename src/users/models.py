"""DB tables for users."""
from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.models import BaseModel


class User(AbstractUser, BaseModel):
    """Chiliseed user object."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
    )
