from decimal import Decimal

from django.db.models import Q

from budget.utils import get_effective_price
from foodCreate.models import Products
from search.services import filter_products
from voice.parser import CURRENCY


def _serialize_product(product):
    image = product.images.first()
    return {
        "id": product.id,
        "title": product.title,
        "price": float(product.price),
        "shop": product.shop.name if product.shop else "",
        "image_url": image.product_image.url if image and image.product_image else "",
        "url": product.get_absolute_url(),
    }


def product_search(entities, *, user=None, nearby_only=False):
    query_terms = []
    if entities.get("query"):
        query_terms.append(entities["query"])
    if entities.get("items"):
        query_terms.extend(entities["items"])

    query = " ".join(query_terms) if query_terms else ""
    max_price = entities.get("max_price")

    queryset = filter_products(
        query=query,
        price_max=max_price,
        nearby_only=nearby_only,
        user=user,
    )

    return [_serialize_product(product) for product in queryset[:20]]


def budget_plan(entities):
    items = entities.get("items") or []
    amount = Decimal(str(entities.get("amount", 0)))
    bundles = []
    if not items or amount <= 0:
        return bundles, "Please say your budget amount in pounds", [], []

    selected_items = []
    selected_products = []
    missing_items = []
    total = Decimal("0.00")

    for item in items:
        candidate = (
            Products.objects.filter(is_active=True)
            .filter(Q(title__icontains=item) | Q(description__icontains=item))
            .order_by("price")
            .first()
        )
        if not candidate:
            missing_items.append(item)
            continue
        price = Decimal(str(get_effective_price(candidate)))
        image = candidate.images.first()
        selected_items.append({
            "id": candidate.id,
            "title": candidate.title,
            "price": float(price),
            "shop": candidate.shop.name if candidate.shop else "",
            "image_url": image.product_image.url if image and image.product_image else "",
            "url": candidate.get_absolute_url(),
        })
        selected_products.append(candidate)
        total += price

    if not selected_items:
        return bundles, "", [], missing_items

    if total > amount:
        return bundles, "That bundle is over budget. Try increasing your budget or removing an item.", [], missing_items

    bundles.append({
        "total": float(total),
        "currency": CURRENCY,
        "items": selected_items,
    })

    return bundles, "", selected_products, missing_items
