"""Model related utilities."""
from django.db import models

from common.crypto import get_uuid_hex


class BaseModel(models.Model):
    """Base chiliseed model with default fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # slug is used for api, instead of id, in order to obscure db state
    slug = models.SlugField(max_length=20, null=True, unique=True, db_index=True)

    objects = models.Manager()

    class Meta:
        """Django Meta conf."""

        abstract = True

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None,
    ):
        """Add custom, general behavior to model save method."""
        if not self.slug:
            self.slug = get_uuid_hex()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
