from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from account.models import Shop
from foodCreate.models import Category, Products

from .models import Budget, BudgetTemplate, BudgetTemplateItem, ShoppingListItem


class BudgetPlannerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='shopper@example.com',
            password='pass1234',
        )
        self.client.force_login(self.user)
        self.category = Category.objects.create(name='Seafood')
        self.shop = Shop.objects.create(
            owner=self.user,
            name='Ocean Market',
            description='Fresh fish',
            address='123 Dock Road',
            city=None,
            country=None,
        )
        self.product = Products.objects.create(
            shop=self.shop,
            title='Salmon',
            category=self.category,
            price=Decimal('5000.00'),
            discount_price=Decimal('4500.00'),
        )

    def test_budget_remaining_updates_with_items(self):
        budget = Budget.objects.create(user=self.user, total_budget=Decimal('10000.00'))
        ShoppingListItem.objects.create(budget=budget, product=self.product, quantity=1)
        self.assertEqual(budget.current_spent, Decimal('4500.00'))
        self.assertEqual(budget.remaining_budget, Decimal('5500.00'))

    def test_apply_template_adds_items(self):
        budget = Budget.objects.create(user=self.user, total_budget=Decimal('12000.00'))
        template = BudgetTemplate.objects.create(user=self.user, name='Weekly Plan')
        BudgetTemplateItem.objects.create(template=template, product=self.product, quantity=2)

        response = self.client.get(
            reverse('budget:apply-template', args=[budget.id, template.id])
        )

        self.assertEqual(response.status_code, 302)
        item = ShoppingListItem.objects.get(budget=budget, product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_view_budget_includes_templates(self):
        budget = Budget.objects.create(user=self.user, total_budget=Decimal('7000.00'))
        BudgetTemplate.objects.create(user=self.user, name='Weekend')

        response = self.client.get(reverse('budget:view-budget', args=[budget.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('templates', response.context)
        self.assertEqual(response.context['templates'].count(), 1)
