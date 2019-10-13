from django.contrib.auth.models import AbstractUser

from utils.models import BaseModel


class User(AbstractUser, BaseModel):
    """Chiliseed user object."""
