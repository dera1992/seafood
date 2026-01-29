from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from account.models import Shop
from foodCreate.models import Category, Products


class HomeViewTests(TestCase):
    def test_ad_detail_renders(self):
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
            title="Shrimp",
            category=category,
            price=Decimal("9.99"),
            available=True,
        )
        response = self.client.get(
            reverse("home:ad_detail", args=[product.id, product.slug])
        )
        self.assertEqual(response.status_code, 200)

# Create your tests here.
