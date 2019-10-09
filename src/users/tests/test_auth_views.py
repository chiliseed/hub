from django.contrib.sessions.models import Session
from django.urls import reverse
from djoser.conf import settings as djconf
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class AuthTestCase(APITestCase):

    def setUp(self) -> None:
        self.password = '1234567ASdf'
        self.user = User.objects.create_user(
            username='tester', email='tester@foo.com', password=self.password
        )

    def test_no_login(self):
        url = reverse("users:login")
        resp = self.client.post(
            url, {'username': 'foo', 'password': 'barbar1'}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        self.assertIsNone(self.user.last_login)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
        url = reverse("users:login")
        resp = self.client.post(
            url, {'username': self.user.username, 'password': self.password}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 1)

    def test_logout(self):
        url = reverse("users:login")
        resp = self.client.post(
            url, {'username': self.user.username, 'password': self.password}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 1)

        url2 = reverse("users:logout")
        resp2 = self.client.post(url2)
        self.assertEqual(resp2.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(djconf.TOKEN_MODEL.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)

