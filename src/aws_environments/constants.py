from django.db import models


class Regions(models.TextChoices):
    nvirginia = "us-east-1"
    ohio = "us-east-2"
    ncalifornia = "us-west-1"
    oregon = "us-west-2"
