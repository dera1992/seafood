from django import forms

from .models import Information

class InformationForm(forms.ModelForm):
    # content = forms.TextField(required = True)

    class Meta:
        model = Information
        fields = ('name','subject','email','message')