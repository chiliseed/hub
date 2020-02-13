import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from aws_environments.models import Environment, ExecutionLog, EnvStatus
from users.tests.factories import UserFactory


class CreateEnvTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.login(username=self.user.email, password="Aa123ewq!")
        self.url = reverse("api:aws_env:create_env")

    @patch("control_center.scheduler.scheduler.add_job")
    def test_happy_flow(self, mocked_scheduler):
        self.assertIsNotNone(self.user.organization)
        self.assertEqual(Environment.objects.count(), 0)
        self.assertEqual(ExecutionLog.objects.count(), 0)

        payload = dict(
            name="test",
            region="us-east-1",
            domain="test.com",
            access_key="123asdfg",
            access_key_secret="asdfasdfasdfasdf",
        )
        resp = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Environment.objects.count(), 1)
        self.assertEqual(ExecutionLog.objects.count(), 1)
        mocked_scheduler.assert_called_once()

        env = Environment.objects.first()
        self.assertEqual(env.name, payload["name"])
        conf = env.conf()
        self.assertEqual(conf.access_key_id, payload["access_key"])
        self.assertEqual(env.last_status.status, EnvStatus.Statuses.changes_pending)

        json_resp = resp.json()
        env = json_resp["env"]
        self.assertEqual(env["name"], payload["name"])
        self.assertEqual(env["region"], payload["region"])
        self.assertTrue(payload["access_key"].encode() not in resp.content)
        self.assertTrue(payload["access_key_secret"].encode() not in resp.content)

        log_slug = json_resp["log"]
        log = ExecutionLog.objects.first()
        self.assertEqual(log_slug, log.slug)
        self.assertEqual(log.action, ExecutionLog.ActionTypes.create)
        self.assertEqual(log.params, json.dumps(payload))


class ListEnvTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.login(username=self.user.email, password="Aa123ewq!")
        self.url = reverse("api:aws_env:list_envs")

    def test_list_envs(self):
        env = Environment.objects.create(
            name="test",
            region="us-east-1",
            domain="test.com",
            organization=self.user.organization,
        )
        resp = self.client.get(self.url, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["name"], env.name)
