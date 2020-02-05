from django.contrib.sessions.models import Session
from django.urls import reverse

from djoser.conf import settings as djconf

from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class AuthTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.password = "Aa123ewq!"

    def test_no_login(self):
        url = reverse("users:login")
        resp = self.client.post(url, {"email": "foo", "password": "barbar1"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        self.assertIsNone(self.user.last_login)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
        url = reverse("users:login")
        resp = self.client.post(
            url, {"email": self.user.email, "password": self.password}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 1)

    def test_logout(self):
        url = reverse("users:login")
        resp = self.client.post(
            url, {"email": self.user.email, "password": self.password}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 1)

        url2 = reverse("users:logout")
        resp2 = self.client.post(url2)
        self.assertEqual(resp2.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
