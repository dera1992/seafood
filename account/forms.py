from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model
from  bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from .models import Profile, Shop, DispatcherProfile, SubscriptionPlan

User = get_user_model()



from .models import Profile

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter First Name', 'label': ''}
        )
    )
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter Last Name', }
        )
    )
    password = forms.CharField(
         widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password'}
        ))
    password2 = forms.CharField(
         widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Repeat Password'}
        ))
    phone_number = forms.CharField(help_text=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Phone Number'}
        ))
    email = forms.EmailField(
       widget=forms.EmailInput(
           attrs={'class': 'form-control', 'placeholder': 'Email'}
       ))

    class Meta:
        model = User
        fields = ('phone_number','email','first_name', 'last_name',)
    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if User.objects.filter(username=username).exists():
    #         raise forms.ValidationError("This username is already used")
    #
    #     return username


    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already used")

        return email

class ProfileForm(forms.ModelForm):
    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'eg: +234 8030793112','label':''}
        )
    )
    address = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter Address'}
        ), required=False,
    )

    class Meta:
        model = Profile
        fields = ('phone','address', 'city', 'postal_code',)


class UserEditForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        del self.fields['password']

    class Meta:
        model = User
        fields = ('phone_number','email','first_name','last_name')
        help_texts = {
            'username': None,
        }

# class UserEditForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ('username', 'email','first_name', 'last_name',)

    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if User.objects.filter(username=username).exists():
    #         raise forms.ValidationError("This username is already used")
    #
    #     return username
    #
    #
    # def clean_email(self):
    #     email = self.cleaned_data.get('email')
    #
    #     if User.objects.filter(email=email).exists():
    #         raise forms.ValidationError("This email is already used")
    #
    #     return email

class ProfileEditForm(forms.ModelForm):
    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'eg: +234 8030793112'}
        )
    )

    address = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter Address'}
        ), required=False
    )
    description = forms.CharField(widget=forms.Textarea(attrs={"rows":5, "cols":20})
                                  ,label='About', required=False)

    class Meta:
        model = Profile
        fields = ('phone', 'address', 'photo','date_of_birth','description')
        # widgets = {
        #     'date_of_birth': DatePickerInput(),
        # }

    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['photo'].widget.attrs.update({'class': 'filestyle'})

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))

# account/forms.py

# Activation is separate; signup already exists

class ShopInfoForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'logo', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ShopAddressForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['address', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude']


class ShopDocumentForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['business_document']


class PlanSelectionForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=SubscriptionPlan.objects.all(), required=False, empty_label="Free plan (default)")


class DispatcherPersonalForm(forms.ModelForm):
    class Meta:
        model = DispatcherProfile
        fields = ['full_name', 'id_number', 'id_document']


class DispatcherVehicleForm(forms.ModelForm):
    class Meta:
        model = DispatcherProfile
        fields = ['vehicle_type', 'plate_number']

