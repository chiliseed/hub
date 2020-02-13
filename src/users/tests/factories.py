from django.contrib.auth.hashers import make_password
from factory import SubFactory, LazyFunction, Faker
from factory.django import DjangoModelFactory

from organizations.tests.factories import OrganizationFactory
from users.models import User


class UserFactory(DjangoModelFactory):
    organization = SubFactory(OrganizationFactory)
    password = LazyFunction(lambda: make_password("Aa123ewq!"))
    email = Faker("email")

    class Meta:
        model = User
        django_get_or_create = ("email",)
