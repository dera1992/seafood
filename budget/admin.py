from django.contrib import admin

from .models import Budget, ShoppingListItem


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_budget', 'created_at')
    search_fields = ('user__email', 'user__username')


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'product', 'quantity')
    search_fields = ('product__title',)
