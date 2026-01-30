from django import forms
from .models import Order
from .models import State,Lga

class OrderCreateForm(forms.ModelForm):
    ref_code = forms.CharField(required=False,
                                initial=False,
                                widget=forms.HiddenInput)
    class Meta:
        model = Order
        fields = ['ref_code']

PAYMENT_CHOICES = (
    ('T', 'Transfer'),
    ('0', 'Online Payment')
)

class CheckoutForm(forms.Form):
    street_address = forms.CharField()
    apartment_address = forms.CharField(required=False)
    same_billing_address = forms.BooleanField(required=False,widget=forms.CheckboxInput())
    save_info = forms.BooleanField(required=False,widget=forms.CheckboxInput())
    state = forms.ModelChoiceField(queryset=State.objects.all(), to_field_name='id')
    city = forms.ModelChoiceField(queryset=Lga.objects.all(), to_field_name='id')
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = Lga.objects.none()

        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = Lga.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        # elif self.instance.pk:
        #     self.fields['city'].queryset = self.instance.state.city.order_by('name')

class CouponForm(forms.Form):
    code = forms.CharField()


class OrderTrackingForm(forms.Form):
    ref = forms.CharField(label="Reference code")


STATUS_CHOICES = (
    ("placed", "Order placed"),
    ("payment_confirmed", "Payment confirmed"),
    ("preparing", "Preparing order"),
    ("out_for_delivery", "Out for delivery"),
    ("delivered", "Delivered"),
)


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(choices=STATUS_CHOICES)
