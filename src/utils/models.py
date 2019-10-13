from hashlib import blake2b
from uuid import uuid4

from django.db import models


class BaseModel(models.Model):
    """Base chiliseed model with default fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # slug is used for api, instead of id, in order to obscure db state
    slug = models.SlugField(max_length=20, null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.slug = blake2b(uuid4().bytes, digest_size=10).hexdigest()
        super().save(*args, **kwargs)
