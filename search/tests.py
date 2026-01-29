from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from account.models import Shop
from foodCreate.models import Category, Products


class SearchViewTests(TestCase):
    def test_invalid_order_does_not_error(self):
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
        Products.objects.create(
            shop=shop,
            title="Item",
            category=category,
            price=Decimal("4.00"),
        )
        response = self.client.get(
            reverse("product_search:product_filter"),
            {"order": "invalid"},
        )
        self.assertEqual(response.status_code, 200)

# Create your tests here.
