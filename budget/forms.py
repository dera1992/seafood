from django import forms

from .models import Budget, BudgetTemplate, BudgetTemplateItem, ShoppingListItem


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['total_budget']
        widgets = {
            'total_budget': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ShoppingListItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingListItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class BudgetTemplateForm(forms.ModelForm):
    class Meta:
        model = BudgetTemplate
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BudgetTemplateItemForm(forms.ModelForm):
    class Meta:
        model = BudgetTemplateItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
