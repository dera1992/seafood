from django.contrib.auth import get_user_model
from django.test import TestCase

from account.models import Shop
from .models import Message


class ChatModelTests(TestCase):
    def test_message_str(self):
        user = get_user_model().objects.create_user(
            email="sender@example.com",
            password="password123",
        )
        receiver = get_user_model().objects.create_user(
            email="receiver@example.com",
            password="password123",
        )
        shop = Shop.objects.create(
            owner=user,
            name="Shop",
            description="Desc",
            address="123 Street",
        )
        message = Message.objects.create(
            shop=shop,
            sender=user,
            receiver=receiver,
            content="Hello",
        )
        self.assertEqual(str(message), "sender@example.com -> receiver@example.com")

# Create your tests here.
