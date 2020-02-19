import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from aws_environments.constants import InfraStatus
from aws_environments.models import Environment, ExecutionLog, Project, ProjectStatus, Service
from aws_environments.tests.factories import EnvironmentFactory, ProjectFactory, ServiceFactory
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory


class CreateEnvTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.login(username=self.user.email, password="Aa123ewq!")
        self.url = reverse("api:aws_env:create_env")

    def test_happy_flow(self):
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

        env = Environment.objects.first()
        self.assertEqual(env.name, payload["name"])
        conf = env.conf()
        self.assertEqual(conf.access_key_id, payload["access_key"])
        self.assertEqual(env.last_status.status, InfraStatus.changes_pending)

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

    def test_invalid_domain(self):
        self.assertEqual(Environment.objects.count(), 0)
        self.assertEqual(ExecutionLog.objects.count(), 0)

        payload = dict(
            name="test",
            region="us-east-1",
            domain="test",
            access_key="123asdfg",
            access_key_secret="asdfasdfasdfasdf",
        )
        resp = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Environment.objects.count(), 0)
        self.assertEqual(ExecutionLog.objects.count(), 0)
        self.assertTrue("Enter a valid URL." in resp.json()["domain"][0])


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


# class CreateListProjectTestCase(APITestCase):
#     def setUp(self) -> None:
#         self.user = UserFactory()
#         self.env = EnvironmentFactory(organization=self.user.organization)
#         self.env.set_status(InfraStatus.ready, None)
#         self.client.login(username=self.user.email, password="Aa123ewq!")
#         self.url = reverse("api:aws_env:projects", args=(self.env.slug,))
#
#     @patch("aws_environments.jobs.create_project_infra.delay")
#     def test_happy_flow(self, mocked_create_project):
#         self.assertEqual(Project.objects.count(), 0)
#
#         payload = dict(name="foofie")
#         resp = self.client.post(self.url, payload, format="json")
#
#         self.assertEqual(resp.status_code, 201)
#         mocked_create_project.assert_called_once()
#
#         self.assertEqual(Project.objects.count(), 1)
#         project = Project.objects.first()
#         self.assertEqual(project.slug, resp.json()["project"]["slug"])
#         self.assertEqual(
#             project.last_status.status, resp.json()["project"]["last_status"]["status"]
#         )
#         self.assertEqual(project.last_status.status, InfraStatus.changes_pending)
#
#     def test_non_existent_env(self):
#         self.assertEqual(Project.objects.count(), 0)
#
#         payload = dict(name="foofie")
#         resp = self.client.post(
#             reverse("api:aws_env:projects", args=("foofie",)), payload, format="json"
#         )
#         self.assertEqual(resp.status_code, 404)
#         self.assertEqual(Project.objects.count(), 0)
#
#     def test_empty_list(self):
#         url = reverse("api:aws_env:projects", args=(self.env.slug,))
#
#         self.assertEqual(Project.objects.count(), 0)
#         resp = self.client.get(url, format="json")
#
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(len(resp.json()), 0)
#
#     def test_cannot_view_not_your_projects(self):
#         org2 = OrganizationFactory(name="foofie")
#         user2 = UserFactory(
#             email="foofie@test.com", username="foofie@test.com", organization=org2
#         )
#         self.assertNotEqual(user2.organization, self.user.organization)
#
#         env2 = EnvironmentFactory(organization=user2.organization)
#         ProjectFactory(organization=user2.organization, environment=env2)
#
#         url = reverse("api:aws_env:projects", args=(env2.slug,))
#         resp = self.client.get(url, format="json")
#         self.assertEqual(resp.status_code, 404)
#
#
class CreateListServiceTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.env = EnvironmentFactory(organization=self.user.organization)
        self.env.set_status(InfraStatus.ready, None)
        self.project = ProjectFactory(organization=self.user.organization, environment=self.env)
        self.client.login(username=self.user.email, password="Aa123ewq!")
        self.url = reverse("api:aws_env:services", args=(self.project.slug, ))

    def test_empty_list(self):
        self.assertEqual(Service.objects.count(), 0)

        resp = self.client.get(self.url, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 0)
#
#     def test_list(self):
#         service = ServiceFactory(project=self.project)
#
#         resp = self.client.get(self.url, format="json")
#         self.assertEqual(resp.status_code, 200)
#         resp_data = resp.json()
#         self.assertEqual(len(resp_data), 1)
#         self.assertEqual(resp_data[0]["slug"], service.slug)
#
#     @patch("aws_environments.jobs.create_service_infra.delay")
#     def test_create_service(self, mocked_create_service):
#         self.assertEqual(Service.objects.count(), 0)
#
#         payload = dict(
#             name="test",
#             subdomain="test",
#             container_port=8000,
#             alb_port_http=80,
#             alb_port_https=443,
#             health_check_endpoint="/foo/test"
#         )
#
#         resp = self.client.post(self.url, payload, format="json")
#         self.assertEqual(resp.status_code, 201)
#
#         service = Service.objects.first()
#         self.assertEqual(service.slug, resp.json()['service']['slug'])
#         mocked_create_service.assert_called_once()
#         self.assertEqual(resp.json()['log'], 1)
