from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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

    def test_get_status_label_defaults_to_placed(self):
        self.assertEqual(self.order.get_status_label(), "Order placed")

    def test_order_tracking_view_shows_status(self):
        self.order.paid = True
        self.order.save()
        response = self.client.get(
            reverse("order:tracking_detail", args=[self.order.ref])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status_label"], "Payment confirmed")
        self.assertTrue(response.context["tracking_steps"])

    def test_staff_can_update_order_status(self):
        staff_user = get_user_model().objects.create_user(
            email="staff@example.com",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(staff_user)
        response = self.client.post(
            reverse("order:update_status", args=[self.order.id]),
            {"status": "delivered"},
        )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_ordered)
        self.assertTrue(self.order.being_delivered)
        self.assertTrue(self.order.received)
        self.assertTrue(self.order.paid)

    def test_non_staff_cannot_update_order_status(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("order:update_status", args=[self.order.id]),
            {"status": "delivered"},
        )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertFalse(self.order.received)
