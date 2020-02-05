from django.urls import reverse
from rest_framework.test import APITestCase

from aws_environments.models import Environment
from users.tests.factories import UserFactory


class CreateEnvTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.login(username=self.user.email, password="Aa123ewq!")
        self.url = reverse("aws_env:create_env")

    def test_happy_flow(self):
        self.assertIsNotNone(self.user.organization)
        self.assertEqual(Environment.objects.count(), 0)

        payload = dict(
            name="test",
            region="us-east-1",
            domain="test@com",
            access_key="123asdfg",
            access_key_secret="asdfasdfasdfasdf",
        )
        resp = self.client.post(self.url, data=payload, format="json")
        print(resp.json())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Environment.objects.count(), 1)

        env = Environment.objects.first()
        self.assertEqual(env.name, payload['name'])
        conf = env.conf()
        self.assertEqual(conf.access_key_id, payload['access_key'])

        env = resp.json()
        self.assertEqual(env['name'], payload['name'])
        self.assertEqual(env['region'], payload['region'])
        self.assertTrue(payload['access_key'].encode() not in resp.content)
        self.assertTrue(payload['access_key_secret'].encode() not in resp.content)
