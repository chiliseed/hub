from django.test import TestCase

from organizations.models import Organization
from users.models import User
from users.serializers import UserCreateSerializer


class UserModelTestCase(TestCase):
    def test_create_new_user(self):
        email = "foo@bar.com"
        u = User.objects.create_user(username="tester", email=email)
        self.assertEqual(u.email, email)
        self.assertIsNotNone(u.slug)

    def test_create_serializer_happy(self):
        data = dict(
            email="foo@bar.com",
            password="Aa1234!@#",
            re_password="Aa1234!@#",
            organization="Test",
        )
        serializer = UserCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Organization.objects.count(), 0)
        user = serializer.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(user.organization.name, data["organization"])
