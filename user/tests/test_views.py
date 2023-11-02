from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model


User = get_user_model()


class ViewTests(TestCase):

    def setUp(self) -> None:
        user = User.objects.create_user(username="testuser", email="test@email.com", password="testpassword")

    def test_login_status_code(self):
        data = {"username": "testuser", "password": "testpassword"}
        c = Client()
        response = c.login(username="testuser", password="testpassword")
        self.assertEqual(response, True)

