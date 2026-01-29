from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware

from account.models import Shop
from foodCreate.models import Category, Products
from .cart import Cart


class CartTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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
            price=Decimal("10.50"),
        )

    def _get_request(self):
        request = self.factory.get("/")
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_cart_total_uses_decimal(self):
        request = self._get_request()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        total = cart.get_total_price()
        self.assertEqual(total, Decimal("21.00"))

# Create your tests here.
