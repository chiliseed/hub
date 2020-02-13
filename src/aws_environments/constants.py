from django.db import models


class Regions(models.TextChoices):
    nvirginia = "us-east-1"
    ohio = "us-east-2"
    ncalifornia = "us-west-1"
    oregon = "us-west-2"


class InfraStatus(models.TextChoices):
    changes_pending = "changes_pending", "Pending changes"
    ready = "ready", "Ready"
    error = "error", "Failed to apply changes"
