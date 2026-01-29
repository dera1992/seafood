from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import OrderItem, Order, Lga, Address, State, Coupon
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, DetailView, View
from .forms import OrderCreateForm, CheckoutForm, CouponForm
from cart.cart import Cart
from order.extras import generate_order_id
from account.models import Profile
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from foodCreate.models import Products, ProductsImages, Category, SubCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http import HttpRequest, HttpResponse


from datetime import date

import random
import string

from django.core.mail import EmailMessage
from django.template.loader import get_template


# Create your views here.

@login_required()
def order_create(request):
    return render(request, 'owner/checkout.html')

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, is_ordered=False)
            form = CheckoutForm()
            states = State.objects.all()
            cities = Lga.objects.all()
            context = {
                'form': form,
                'order': order,
                'states':states,
                'cities':cities
            }
            return render(self.request, "owner/checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("order:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, is_ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                state = form.cleaned_data.get('state')
                city = form.cleaned_data.get('city')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = Address(
                    user = self.request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    state = state,
                    city = city
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == '0':
                    return redirect('order:payment', payment_option='online payment')
                elif payment_option == 'T':
                    return redirect('order:transfer')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('order:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("cart:order-summary")

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, is_ordered=False)
        amount = order.get_total()
        email = order.user.email
        if order.billing_address:
            context = {
                'order': order,
                'amt':amount,
                'amount':amount * 100,
                'email':email,
                'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY

            }
            return render(self.request, "owner/payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("cart:order-summary")

    def post(self, *args, **kwargs):

        return redirect("/payment/stripe/")

@login_required
def order_owner(request):
    order_list = Order.objects.filter(user=request.user)
    lates = Products.objects.all().order_by('-created_date')[:3]
    counts = Products.objects.all().values('category__name').annotate(total=Count('category'))

    today = date.today()

    my_order = Order.objects.filter(user=request.user,created__day=today.day)

    paginator = Paginator(order_list, 6)
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        allorder = paginator.page(page)
    except PageNotAnInteger:
        allorder = paginator.page(1)
    except EmptyPage:
        allorder = paginator.page(paginator.num_pages)
    return render(request, 'owner/order_list.html', {'allorder': allorder,'lates': lates,
                                                 'counts': counts, 'page_request_var': page_request_var,
                                                 'my_order':my_order})

@login_required
def order_all(request):
    order_list = Order.objects.all()
    print(order_list)
    lates = Products.objects.all().order_by('-created_date')[:3]
    counts = Products.objects.all().values('category__name').annotate(total=Count('category'))

    today = date.today()

    today_order = Order.objects.filter(created__day=today.day)
    pending_order = Order.objects.filter(created__day=today.day)
    delivered_order = Order.objects.filter(created__day=today.day, being_delivered=True)
    paid_order = Order.objects.filter(paid=True,created__day=today.day)

    paginator = Paginator(order_list, 6)
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        allorder = paginator.page(page)
    except PageNotAnInteger:
        allorder = paginator.page(1)
    except EmptyPage:
        allorder = paginator.page(paginator.num_pages)
    return render(request, 'owner/order_list.html', {'allorder': allorder,'lates': lates,
                                                 'counts': counts, 'page_request_var': page_request_var,
                                                 'today_order': today_order,'paid_order':paid_order,
                                                  'pending_order':pending_order,'delivered_order':delivered_order})

def load_cities(request):
    state_id = request.GET.get('state')
    cities = Lga.objects.filter(state_id=state_id).order_by('name')
    return render(request, 'owner/city_dropdown_list_options.html', {'cities': cities})


@login_required
def transfer(request):
    try:
        order = Order.objects.get(user=request.user, is_ordered=False)

        order_items = order.items.all()
        order_items.update(is_ordered=True)
        for item in order_items:
            item.save()

        order.is_ordered = True
        # order.ref = create_ref_code()
        order.save()
        messages.warning(
            request, "Make your payment and your product will get to you")
        return redirect('order:order_owner')
    except ObjectDoesNotExist:
        messages.warning(request, "You do not have an active order")
        return redirect("cart:order-summary")


def verify_payment(request:HttpRequest, ref:str) -> HttpResponse:
    payment = get_object_or_404(Order, ref=ref)
    order_items = payment.items.all()
    order_items.update(is_ordered=True)
    for item in order_items:
        item.save()
    verified = payment.verify_payment()
    if verified:
        subject = 'Payment Successful'
        message = get_template('paystack/success-page.html').render({
            'payment': payment,
        })
        to_email = [payment.user.email]
        email = EmailMessage(
            subject, message, from_email='Bunchfood <bunchfood@gmail.com>', to=to_email
        )
        email.content_subtype = 'html'
        email.send()
        messages.success(request, "Payment Verifiction Successful")
        # return render(request, 'paystack/success-page.html', )
    else:
        subject = 'Payment Failed'
        message = get_template('paystack/failed-page.html').render({
            'payment': payment,
        })
        to_email = [payment.user.email]
        email = EmailMessage(
            subject, message, from_email='Bunchfood <bunchfood@gmail.com>', to=to_email
        )
        email.content_subtype = 'html'
        email.send()
        messages.error(request, "Payment Verification Failed")
    return redirect("order:order_owner")

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("cart:order-summary")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, is_ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("cart:order-summary")
            except ObjectDoesNotExist:
                messages.info(self.request, "This coupon does not exist")
                return redirect("cart:order-summary")
