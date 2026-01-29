from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from account.models import Shop
from .models import Category, Products


class ProductsModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="seller@example.com",
            password="password123",
        )
        self.shop = Shop.objects.create(
            owner=self.user,
            name="Shop",
            description="Desc",
            address="123 Street",
        )
        self.category = Category.objects.create(name="Category")

    def test_unique_slug_per_shop(self):
        product1 = Products.objects.create(
            shop=self.shop,
            title="Fresh Fish",
            category=self.category,
            price=Decimal("5.00"),
        )
        product2 = Products.objects.create(
            shop=self.shop,
            title="Fresh Fish",
            category=self.category,
            price=Decimal("6.00"),
        )
        self.assertNotEqual(product1.slug, product2.slug)

# Create your tests here.
