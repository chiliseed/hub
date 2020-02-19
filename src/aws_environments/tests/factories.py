from faker import Faker
from factory.django import DjangoModelFactory

from aws_environments.models import Environment, Project, Service

fake = Faker()


class EnvironmentFactory(DjangoModelFactory):
    name = fake.word(ext_word_list=None)

    class Meta:
        model = Environment


class ProjectFactory(DjangoModelFactory):
    name = fake.word(ext_word_list=None)

    class Meta:
        model = Project


class ServiceFactory(DjangoModelFactory):
    name = fake.word(ext_word_list=None)
    subdomain = fake.word(ext_word_list=None)

    class Meta:
        model = Service
