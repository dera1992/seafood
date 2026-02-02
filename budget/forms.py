from django import forms

from foodCreate.models import Products

from .models import Budget, BudgetTemplate, BudgetTemplateItem, ShoppingListItem


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['total_budget']
        widgets = {
            'total_budget': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ShoppingListItemForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        name = (cleaned_data.get('name') or '').strip()

        if not product and not name:
            raise forms.ValidationError('Select a product or enter a custom item name.')
        cleaned_data['name'] = name
        return cleaned_data

    class Meta:
        model = ShoppingListItem
        fields = ['product', 'name', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control', 'data-searchable-select': 'true'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Custom item name',
                'id': 'shopping-list-name',
            }),
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


class ShoppingListItemQuantityForm(forms.ModelForm):
    class Meta:
        model = ShoppingListItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 1}),
        }
