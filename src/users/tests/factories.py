from django.contrib.auth.hashers import make_password
from factory import SubFactory, LazyFunction
from factory.django import DjangoModelFactory
from faker import Faker

from organizations.tests.factories import OrganizationFactory
from users.models import User

fake = Faker()


class UserFactory(DjangoModelFactory):
    organization = SubFactory(OrganizationFactory)
    password = LazyFunction(lambda: make_password("Aa123ewq!"))
    email = fake.company_email()
    username = fake.company_email()

    class Meta:
        model = User
