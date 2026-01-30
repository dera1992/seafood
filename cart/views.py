from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import View
from foodCreate.models import Products
from order.forms import CouponForm
from order.models import Order,OrderItem
from .cart import Cart
from .forms import CartAddProductForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from budget.models import Budget



@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Products, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 update_quantity=cd['update'])
    return redirect('cart:cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Products, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    # products = []
    # for item in cart:
    #     item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'],
    #                                                                'update': True})
        # products.append(item)
    context = {
        'cart': cart,
        'active_budget': Budget.get_active_for_user(request.user),
    }
    # context['products'] = products
    return render(request, 'owner/cart.html', context)


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, is_ordered=False)
            context = {
                'cart': order,
                'couponform': CouponForm(),
                'active_budget': Budget.get_active_for_user(self.request.user),
            }
            return render(self.request, 'owner/cart.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Products, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        is_ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("cart:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return HttpResponseRedirect(item.get_absolute_url())
    else:
        order = Order.objects.create(
            user=request.user)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return HttpResponseRedirect(item.get_absolute_url())

@login_required
def add_to_cart_ajax(request):
    item = get_object_or_404(Products,id=request.POST.get('id'))
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        is_ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__id=item.id).exists():
            order_item.quantity += 1
            order_item.save()
            return JsonResponse({'status':'ok'})
        else:
            order.items.add(order_item)
            return JsonResponse({'status':'ook'})
    else:
        order = Order.objects.create(
            user=request.user)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return JsonResponse({'status':'ko'})


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Products, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        is_ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                is_ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("cart:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("home:ad_detail", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("home:ad_detail", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Products, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        is_ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                is_ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("cart:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)
