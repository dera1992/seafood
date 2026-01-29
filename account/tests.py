from django.contrib.auth import get_user_model
from django.test import TestCase


class AccountModelTests(TestCase):
    def test_create_user_with_email(self):
        user = get_user_model().objects.create_user(
            email="user@example.com",
            password="password123",
        )
        self.assertEqual(user.email, "user@example.com")

# Create your tests here.
