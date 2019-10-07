from hashlib import blake2b
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Chiliseed user object."""

    slug = models.SlugField(max_length=20, null=True)

    def save(self, *args, **kwargs):
        self.slug = blake2b(uuid4().bytes, digest_size=10).hexdigest()
        super().save(*args, **kwargs)
