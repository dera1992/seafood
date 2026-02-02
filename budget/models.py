from decimal import Decimal

from django.conf import settings
from django.db import models

from foodCreate.models import Products


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_budget = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user} budget {self.total_budget}"

    @property
    def current_spent(self) -> Decimal:
        return sum((item.total_cost for item in self.items.all()), Decimal('0.00'))

    @property
    def remaining_budget(self) -> Decimal:
        return self.total_budget - self.current_spent

    @classmethod
    def get_active_for_user(cls, user):
        if not user.is_authenticated:
            return None
        return cls.objects.filter(user=user).order_by('-created_at').first()


class ShoppingListItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, default="")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('budget', 'product', 'name')

    def __str__(self) -> str:
        if self.product:
            return f"{self.quantity} x {self.product.title}"
        if self.name:
            return f"{self.quantity} x {self.name}"
        return f"{self.quantity} x item"

    @property
    def unit_price(self) -> Decimal:
        if not self.product:
            return Decimal("0.00")
        if self.product.discount_price:
            return self.product.discount_price
        return self.product.price

    @property
    def total_cost(self) -> Decimal:
        return self.unit_price * self.quantity


class BudgetTemplate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.user})"


class BudgetTemplateItem(models.Model):
    template = models.ForeignKey(BudgetTemplate, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('template', 'product')

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product.title}"
