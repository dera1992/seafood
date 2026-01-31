# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.core.files.uploadedfile import UploadedFile
import csv
from io import TextIOWrapper
import importlib.util

openpyxl = None
if importlib.util.find_spec("openpyxl"):
    openpyxl = importlib.import_module("openpyxl")

from .models import Products, ProductsImages, Category, SubCategory
from .forms import AdsForm, AdsEditForm

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

    if request.method == 'POST':
        post_form = AdsForm(request.POST, request.FILES, currency=shop.currency)

        if post_form.is_valid():
            product = post_form.save(commit=False)
            product.shop = shop
            if request.POST.get("save_draft"):
                product.status = "draft"
                product.is_active = False
            elif product.status != "draft":
                product.is_active = True
            product.save()

            images = request.FILES.getlist("product_images")
            for image in images:
                photo = ProductsImages(products=product, product_image=image)
                photo.save()  # compression happens here
            messages.success(request, "Your product has been created successfully.")
            return redirect('home:allads_list')
        else:
            messages.error(request, "Error creating your product.")
    else:
        post_form = AdsForm(currency=shop.currency)

    template_products = Products.objects.filter(shop=shop).order_by("title")
    categories = list(Category.objects.values("id", "name"))

    return render(
        request,
        'advert/post.html',
        {
            'postForm': post_form,
            'template_products': template_products,
            'categories': categories,
            'shop_currency': shop.currency,
            'shop_weight_unit': shop.weight_unit,
        }
    )


@login_required
@transaction.atomic
def editAd(request, pk):
    """Edit an existing product."""
    product = get_object_or_404(Products, pk=pk)
    shop = request.user.shops.first()

    if not shop or product.shop != shop:
        raise Http404("You are not authorized to edit this product.")

    if request.method == 'POST':
        post_form = AdsEditForm(request.POST, request.FILES, instance=product, currency=shop.currency)

        if post_form.is_valid():
            post_form = post_form.save(commit=False)
            post_form.shop = product.shop
            if request.POST.get("save_draft"):
                post_form.status = "draft"
                post_form.is_active = False
            elif post_form.status != "draft":
                post_form.is_active = True
            post_form.save()

            delete_image_ids = request.POST.getlist("delete_image_ids")
            for image in product.images.all():
                if str(image.id) in delete_image_ids:
                    image.delete()
                    continue
                replacement = request.FILES.get(f"replace_image_{image.id}")
                if replacement:
                    image.product_image = replacement
                    image.save()

            images = request.FILES.getlist("product_images")
            for image in images:
                photo = ProductsImages(products=product, product_image=image)
                photo.save()  # compression automatically applied

            messages.success(request, f"{product.title} has been successfully updated!")
            return redirect('home:allads_list')
        else:
            messages.error(request, "Error updating your product.")
    else:
        post_form = AdsEditForm(instance=product, currency=shop.currency)

    template_products = Products.objects.filter(shop=shop).order_by("title")
    categories = list(Category.objects.values("id", "name"))

    return render(
        request,
        'advert/post.html',
        {
            'postForm': post_form,
            'product': product,
            'template_products': template_products,
            'categories': categories,
            'shop_currency': shop.currency,
            'shop_weight_unit': shop.weight_unit,
        }
    )


def load_subcategories(request):
    """AJAX loader for dynamic subcategory selection."""
    category_id = request.GET.get('category')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    return render(request, 'advert/subcategory_dropdown_list_options.html', {'subcategories': subcategories})


@login_required
@require_GET
def lookup_product(request):
    """Return product details for barcode or template lookups within the user's shop."""
    shop = request.user.shops.first()
    if not shop:
        return JsonResponse({"error": "Shop not found."}, status=404)

    barcode = request.GET.get("barcode")
    template_id = request.GET.get("template_id")
    product = None

    if barcode:
        product = Products.objects.filter(shop=shop, barcode=barcode).first()
    elif template_id:
        product = Products.objects.filter(shop=shop, id=template_id).first()

    if not product:
        return JsonResponse({"found": False})

    return JsonResponse({
        "found": True,
        "title": product.title,
        "category": product.category_id,
        "subcategory": product.subcategory_id,
        "price": str(product.price),
        "discount_price": str(product.discount_price) if product.discount_price else "",
        "description": product.description,
        "label": product.label,
        "status": product.status,
        "delivery": product.delivery,
        "available": product.available,
        "barcode": product.barcode,
        "stock": product.stock,
    })


@login_required
@require_POST
def duplicate_product(request, pk):
    """Duplicate an existing product with its images."""
    product = get_object_or_404(Products, pk=pk)
    shop = request.user.shops.first()

    if not shop or product.shop != shop:
        raise Http404("You are not authorized to duplicate this product.")

    new_product = Products.objects.get(pk=product.pk)
    new_product.pk = None
    new_product.slug = ""
    new_product.title = f"{product.title} (Copy)"
    new_product.save()

    for image in product.images.all():
        if image.product_image:
            ProductsImages.objects.create(
                products=new_product,
                product_image=image.product_image,
            )

    messages.success(request, "Product duplicated successfully.")
    return redirect("foodcreate:edit_post", pk=new_product.pk)


@login_required
def bulk_upload_products(request):
    """Handle CSV/XLSX bulk uploads for products and inventory updates."""
    shop = request.user.shops.first()
    if not shop:
        messages.error(request, "You must create a shop before importing products.")
        return redirect("home:home")

    preview_rows = []
    errors = []
    created_count = 0
    updated_inventory = 0

    if request.method == "POST":
        upload = request.FILES.get("upload_file")
        mode = request.POST.get("upload_mode")

        if not upload:
            messages.error(request, "Please select a CSV or XLSX file to upload.")
        else:
            filename = upload.name.lower()
            if filename.endswith(".csv"):
                rows = _read_csv(upload)
            elif filename.endswith(".xlsx"):
                if not openpyxl:
                    messages.error(request, "XLSX uploads require the openpyxl dependency.")
                    rows = []
                else:
                    rows = _read_xlsx(upload)
            else:
                rows = []
                messages.error(request, "Unsupported file type. Upload CSV or XLSX only.")

            if rows:
                if mode == "inventory":
                    updated_inventory, errors = _handle_inventory_import(shop, rows)
                else:
                    created_count, preview_rows, errors = _handle_product_import(shop, rows)

    return render(
        request,
        "advert/bulk_upload.html",
        {
            "preview_rows": preview_rows,
            "errors": errors,
            "created_count": created_count,
            "updated_inventory": updated_inventory,
        },
    )


def _read_csv(upload: UploadedFile):
    decoded = TextIOWrapper(upload.file, encoding="utf-8")
    reader = csv.DictReader(decoded)
    return list(reader)


def _read_xlsx(upload: UploadedFile):
    workbook = openpyxl.load_workbook(upload, data_only=True)
    sheet = workbook.active
    headers = [str(cell.value).strip() if cell.value else "" for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
    rows = []
    for row in sheet.iter_rows(min_row=2):
        row_data = {}
        for header, cell in zip(headers, row):
            row_data[header] = cell.value
        rows.append(row_data)
    return rows


def _handle_product_import(shop, rows):
    required_fields = {"title", "category", "price"}
    created_count = 0
    preview_rows = []
    errors = []

    for index, row in enumerate(rows, start=1):
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        missing = [field for field in required_fields if not normalized.get(field)]
        if missing:
            errors.append(f"Row {index}: missing required fields: {', '.join(missing)}")
            continue

        category_name = str(normalized.get("category")).strip()
        category = Category.objects.filter(name__iexact=category_name).first()
        if not category:
            errors.append(f"Row {index}: category '{category_name}' not found.")
            continue

        subcategory_name = str(normalized.get("subcategory") or "").strip()
        subcategory = None
        if subcategory_name:
            subcategory = SubCategory.objects.filter(category=category, name__iexact=subcategory_name).first()

        product = Products(
            shop=shop,
            title=str(normalized.get("title")).strip(),
            category=category,
            subcategory=subcategory,
            price=normalized.get("price"),
            discount_price=normalized.get("discount_price") or None,
            description=normalized.get("description") or "",
            label=normalized.get("label") or None,
            status=normalized.get("status") or "available",
            delivery=normalized.get("delivery") or None,
            available=str(normalized.get("available")).lower() in {"true", "1", "yes"},
            barcode=str(normalized.get("barcode") or "").strip(),
            stock=int(normalized.get("stock") or 0),
        )
        product.save()
        created_count += 1
        preview_rows.append({
            "title": product.title,
            "category": category.name,
            "price": product.price,
            "status": product.status,
        })

    return created_count, preview_rows, errors


def _handle_inventory_import(shop, rows):
    errors = []
    updated = 0

    for index, row in enumerate(rows, start=1):
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        barcode = str(normalized.get("barcode") or "").strip()
        stock = normalized.get("stock")

        if not barcode or stock is None:
            errors.append(f"Row {index}: barcode and stock are required.")
            continue

        product = Products.objects.filter(shop=shop, barcode=barcode).first()
        if not product:
            errors.append(f"Row {index}: no product found for barcode {barcode}.")
            continue

        try:
            product.stock = int(stock)
        except (TypeError, ValueError):
            errors.append(f"Row {index}: invalid stock value {stock}.")
            continue

        product.save()
        updated += 1

    return updated, errors
