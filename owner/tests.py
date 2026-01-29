from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from account.models import Shop
from foodCreate.models import Category, Products


class OwnerViewTests(TestCase):
    def test_delete_post_marks_inactive(self):
        user = get_user_model().objects.create_user(
            email="owner@example.com",
            password="password123",
        )
        shop = Shop.objects.create(
            owner=user,
            name="Shop",
            description="Desc",
            address="123 Street",
        )
        category = Category.objects.create(name="Category")
        product = Products.objects.create(
            shop=shop,
            title="Item",
            category=category,
            price=Decimal("3.00"),
        )
        self.client.force_login(user)
        response = self.client.get(reverse("owner:delete_post", args=[product.id]))
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertFalse(product.is_active)

# Create your tests here.
