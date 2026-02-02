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
    product_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Start typing a product'}),
    )
    product_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.product:
            self.fields['product_name'].initial = self.instance.product.title
            self.fields['product_id'].initial = self.instance.product_id
        elif self.instance and self.instance.name:
            self.fields['product_name'].initial = self.instance.name

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        name = (cleaned_data.get('name') or '').strip()
        product_name = (cleaned_data.get('product_name') or '').strip()
        product_id = cleaned_data.get('product_id')

        if not product and product_id:
            product = Products.objects.filter(id=product_id).first()
            cleaned_data['product'] = product

        if not product and product_name:
            product = Products.objects.filter(title__iexact=product_name).first()
            if product:
                cleaned_data['product'] = product

        if not cleaned_data.get('product') and not product_name and not name:
            raise forms.ValidationError('Select a product or enter a custom item name.')
        cleaned_data['name'] = name or product_name
        return cleaned_data

    class Meta:
        model = ShoppingListItem
        fields = ['product', 'name', 'quantity']
        widgets = {
            'product': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Custom item name'}),
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
