from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import OrderItem, Order, Lga, Address, State, Coupon
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, DetailView, View
from .forms import (
    OrderCreateForm,
    CheckoutForm,
    CouponForm,
    OrderTrackingForm,
    OrderStatusForm,
)
from cart.cart import Cart
from order.extras import generate_order_id
from account.models import Profile
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from foodCreate.models import Products, ProductsImages, Category, SubCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from budget.models import Budget


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
    def _sync_budget_items(self, budget_id):
        budget = Budget.objects.filter(id=budget_id, user=self.request.user).first()
        if not budget:
            return None, 0, 0

        order, _ = Order.objects.get_or_create(user=self.request.user, is_ordered=False)
        added_count = 0
        skipped_count = 0
        for item in budget.items.select_related('product').all():
            if not item.product:
                skipped_count += 1
                continue
            order_item, _ = OrderItem.objects.get_or_create(
                user=self.request.user,
                item=item.product,
                is_ordered=False,
            )
            order_item.quantity = item.quantity
            order_item.save()
            order.items.add(order_item)
            added_count += 1

        return order, added_count, skipped_count

    def get(self, *args, **kwargs):
        budget_id = self.request.GET.get('budget')
        if budget_id:
            order, added_count, skipped_count = self._sync_budget_items(budget_id)
            if order:
                if added_count:
                    messages.success(self.request, 'Your shopping list items have been added to the cart.')
                if skipped_count:
                    messages.warning(
                        self.request,
                        'Some custom items could not be added to the cart. Please select products for them.',
                    )
                form = CheckoutForm()
                states = State.objects.all()
                cities = Lga.objects.all()
                context = {
                    'form': form,
                    'order': order,
                    'states': states,
                    'cities': cities,
                }
                return render(self.request, "owner/checkout.html", context)

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
    return render(request, 'owner/order_list.html', {
        'allorder': allorder,
        'lates': lates,
        'counts': counts,
        'page_request_var': page_request_var,
        'my_order': my_order,
        'status_form': OrderStatusForm(),
    })

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
    return render(request, 'owner/order_list.html', {
        'allorder': allorder,
        'lates': lates,
        'counts': counts,
        'page_request_var': page_request_var,
        'today_order': today_order,
        'paid_order': paid_order,
        'pending_order': pending_order,
        'delivered_order': delivered_order,
        'status_form': OrderStatusForm(),
    })

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


def order_tracking(request, ref=None):
    order = None
    tracking_steps = []
    form = OrderTrackingForm(initial={"ref": ref} if ref else None)
    status_label = None
    if request.method == "POST":
        form = OrderTrackingForm(request.POST)
        if form.is_valid():
            ref = form.cleaned_data["ref"]
    if ref:
        try:
            order = Order.objects.get(ref=ref)
            tracking_steps = order.get_tracking_steps()
            status_label = order.get_status_label()
        except Order.DoesNotExist:
            messages.error(request, "We could not find an order with that reference.")
    return render(request, "order/tracking.html", {
        "form": form,
        "order": order,
        "tracking_steps": tracking_steps,
        "status_label": status_label,
    })


@login_required
def update_order_status(request, order_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You do not have permission to update order status.")
        return redirect("order:order_all")
    order = get_object_or_404(Order, id=order_id)
    if request.method != "POST":
        return redirect("order:order_all")
    form = OrderStatusForm(request.POST)
    if form.is_valid():
        status = form.cleaned_data["status"]
        order.is_ordered = status in {"preparing", "out_for_delivery", "delivered"}
        order.being_delivered = status in {"out_for_delivery", "delivered"}
        order.received = status == "delivered"
        if status in {"payment_confirmed", "preparing", "out_for_delivery", "delivered"}:
            order.paid = True
            order.verified = True
        order.save()
        messages.success(request, "Order status updated.")
    return redirect("order:order_all")
