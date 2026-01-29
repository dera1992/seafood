# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db import transaction

from .models import Products, ProductsImages, Category, SubCategory
from .forms import AdsImageForm, AdsForm, AdsEditForm

@login_required
@transaction.atomic
def postAd(request):
    """Create a new product for the shop linked to the current user."""
    user = request.user
    shop = user.shops.first()

    if not shop:
        messages.error(request, "You must create a shop before adding products.")
        return redirect("home:home")

    # Check subscription plan product limit
    product_count = Products.objects.filter(shop=shop).count()
    plan_limit = shop.subscription.product_limit if shop.subscription else 10
    if product_count >= plan_limit:
        messages.warning(
            request,
            f"Your current plan allows only {plan_limit} products. Please upgrade your subscription."
        )
        return redirect("home:home")

    ImageFormSet = modelformset_factory(ProductsImages, form=AdsImageForm, extra=3)

    if request.method == 'POST':
        post_form = AdsForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES, queryset=ProductsImages.objects.none())

        if post_form.is_valid() and formset.is_valid():
            product = post_form.save(commit=False)
            product.shop = shop
            product.save()

            for form in formset.cleaned_data:
                if form:
                    image = form['product_image']
                    photo = ProductsImages(products=product, product_image=image)
                    photo.save()  # compression happens here
            messages.success(request, "Your product has been created successfully.")
            return redirect('home:allads_list')
        else:
            messages.error(request, "Error creating your product.")
    else:
        post_form = AdsForm()
        formset = ImageFormSet(queryset=ProductsImages.objects.none())

    return render(request, 'advert/post.html', {'postForm': post_form, 'formset': formset})


@login_required
@transaction.atomic
def editAd(request, pk):
    """Edit an existing product."""
    product = get_object_or_404(Products, pk=pk)
    shop = request.user.shops.first()

    if not shop or product.shop != shop:
        raise Http404("You are not authorized to edit this product.")

    ImageFormSet = modelformset_factory(ProductsImages, form=AdsImageForm, extra=3)

    if request.method == 'POST':
        post_form = AdsEditForm(request.POST, request.FILES, instance=product)
        formset = ImageFormSet(request.POST, request.FILES, queryset=ProductsImages.objects.filter(products=product))

        if post_form.is_valid() and formset.is_valid():
            post_form = post_form.save(commit=False)
            post_form.shop = product.shop
            post_form.save()

            for form in formset.cleaned_data:
                if form:
                    image = form.get('product_image')
                    if image:
                        photo = ProductsImages(products=product, product_image=image)
                        photo.save()  # compression automatically applied

            messages.success(request, f"{product.title} has been successfully updated!")
            return redirect('home:allads_list')
        else:
            messages.error(request, "Error updating your product.")
    else:
        post_form = AdsEditForm(instance=product)
        formset = ImageFormSet(queryset=ProductsImages.objects.filter(products=product))

    return render(request, 'advert/post.html', {'postForm': post_form, 'formset': formset})


def load_subcategories(request):
    """AJAX loader for dynamic subcategory selection."""
    category_id = request.GET.get('category')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    return render(request, 'advert/subcategory_dropdown_list_options.html', {'subcategories': subcategories})
