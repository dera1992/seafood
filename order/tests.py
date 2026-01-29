from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from account.models import Shop
from foodCreate.models import Category, Products
from .models import Order, OrderItem


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="password123",
        )
        self.shop = Shop.objects.create(
            owner=self.user,
            name="Shop",
            description="Desc",
            address="123 Street",
        )
        self.category = Category.objects.create(name="Category")
        self.product = Products.objects.create(
            shop=self.shop,
            title="Item",
            category=self.category,
            price=Decimal("12.00"),
        )
        self.order_item = OrderItem.objects.create(
            user=self.user,
            item=self.product,
            quantity=1,
        )
        self.order = Order.objects.create(user=self.user)
        self.order.items.add(self.order_item)

    def test_verify_payment_marks_order(self):
        total = self.order.get_total()
        with patch("order.models.PayStack.verify_payment") as verify_payment:
            verify_payment.return_value = (True, {"amount": total * 100})
            verified = self.order.verify_payment()
        self.assertTrue(verified)
        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)

# Create your tests here.
