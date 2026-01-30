from django.contrib import admin

from .models import Budget, BudgetTemplate, BudgetTemplateItem, ShoppingListItem


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_budget', 'created_at')
    search_fields = ('user__email', 'user__username')


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'product', 'quantity')
    search_fields = ('product__title',)


@admin.register(BudgetTemplate)
class BudgetTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'updated_at')
    search_fields = ('name', 'user__email', 'user__username')


@admin.register(BudgetTemplateItem)
class BudgetTemplateItemAdmin(admin.ModelAdmin):
    list_display = ('template', 'product', 'quantity')
    search_fields = ('template__name', 'product__title')
