from faker import Faker
from factory.django import DjangoModelFactory

from aws_environments.models import Environment

fake = Faker()


class EnvironmentFactory(DjangoModelFactory):
    name = fake.word(ext_word_list=None)

    class Meta:
        model = Environment
