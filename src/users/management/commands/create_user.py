from django.core.management.base import BaseCommand

from organizations.models import Organization
from users.models import User


class Command(BaseCommand):
    help = "Create user and organization."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)
        parser.add_argument("organization_name", type=str)
        parser.add_argument(
            "--is-superuser", type=bool, default=False, dest="is_superuser"
        )

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(name=options["organization_name"])
        User.objects.create_user(
            username=options["email"],
            email=options["email"],
            password=options["password"],
            is_superuser=options["is_superuser"],
            is_active=True,
            organization=org,
        )
