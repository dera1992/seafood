from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.conf import settings
from  bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.core.exceptions import ValidationError
import requests

from .models import Profile, Shop, DispatcherProfile, SubscriptionPlan

User = get_user_model()


def verify_recaptcha(token, remote_ip=None):
    if not settings.RECAPTCHA_SECRET_KEY or not settings.RECAPTCHA_SITE_KEY:
        return
    if not token:
        raise ValidationError("Please complete the reCAPTCHA.")
    payload = {
        "secret": settings.RECAPTCHA_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip
    try:
        response = requests.post(
            settings.RECAPTCHA_VERIFY_URL,
            data=payload,
            timeout=5,
        )
        result = response.json()
    except requests.RequestException as exc:
        raise ValidationError("Unable to verify reCAPTCHA. Please try again.") from exc
    if not result.get("success"):
        raise ValidationError("Invalid reCAPTCHA. Please try again.")

class UserRegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password'}
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Repeat Password'}
        )
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'Email'}
        )
    )

    class Meta:
        model = User
        fields = ('email',)
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

    def clean(self):
        cleaned_data = super().clean()
        token = self.data.get("g-recaptcha-response")
        remote_ip = None
        if self.request:
            remote_ip = self.request.META.get("REMOTE_ADDR")
        verify_recaptcha(token, remote_ip=remote_ip)
        return cleaned_data

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


class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'role', 'is_staff', 'is_active')


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'is_staff',
            'is_active',
            'is_superuser',
            'groups',
            'user_permissions',
        )

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
    remember_me = forms.BooleanField(required=False, label="Remember me")

    def clean(self):
        cleaned_data = super().clean()
        token = self.data.get("g-recaptcha-response")
        remote_ip = None
        if self.request:
            remote_ip = self.request.META.get("REMOTE_ADDR")
        verify_recaptcha(token, remote_ip=remote_ip)
        return cleaned_data

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
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput(attrs={"id": "latitude"}),
    )
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput(attrs={"id": "longitude"}),
    )

    class Meta:
        model = Shop
        fields = ['address', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude']

    def clean_latitude(self):
        latitude = self.cleaned_data.get("latitude")
        if latitude is None:
            return latitude
        if latitude < -90 or latitude > 90:
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get("longitude")
        if longitude is None:
            return longitude
        if longitude < -180 or longitude > 180:
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return longitude


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
