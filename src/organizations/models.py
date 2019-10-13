from django.db import models

from utils.models import BaseModel


class Organization(BaseModel):
    """Company represented by a users and projects."""

    name = models.CharField(max_length=254)

    def __str__(self):
        return self.name
