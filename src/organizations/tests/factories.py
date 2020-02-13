from faker import Faker
from factory.django import DjangoModelFactory

from organizations.models import Organization

fake = Faker()


class OrganizationFactory(DjangoModelFactory):
    name = fake.name()

    class Meta:
        model = Organization
        django_get_or_create = ("name",)
