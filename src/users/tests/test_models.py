from django.test import TestCase

from users.models import User


class UserModelTestCase(TestCase):

    def test_create_new_user(self):
        email = 'foo@bar.com'
        u = User.objects.create_user(username='tester', email=email)
        self.assertEqual(u.email, email)
        self.assertIsNotNone(u.slug)
