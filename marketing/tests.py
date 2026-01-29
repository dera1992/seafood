from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Signup


class MarketingModelTests(TestCase):
    def test_unique_email(self):
        Signup.objects.create(email="subscriber@example.com")
        duplicate = Signup(email="subscriber@example.com")
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

# Create your tests here.
