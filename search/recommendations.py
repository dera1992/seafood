from collections import Counter
import re

from account.models import Profile
from foodCreate.models import Products
from order.models import OrderItem, Order


def get_user_location(user):
    profile = Profile.objects.filter(user=user).first()
    latest_order = (
        Order.objects.filter(user=user, is_ordered=True)
        .select_related("billing_address__city", "billing_address__state")
        .order_by("-created")
        .first()
    )
    billing_address = latest_order.billing_address if latest_order else None
    return {
        "city": (billing_address.city.name if billing_address and billing_address.city else None)
        or (profile.city if profile else None),
        "state": (billing_address.state.name if billing_address and billing_address.state else None),
    }


def _tokenize(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def score_product(product, context):
    score = 0
    if product.discount_price:
        score += 2
    if product.category_id in context["preferred_categories"]:
        score += 3 + min(context["category_counts"][product.category_id], 5) * 0.2
    if product.shop_id in context["preferred_shops"]:
        score += 2 + min(context["shop_counts"][product.shop_id], 5) * 0.2
    if product.id in context["purchased_products"]:
        score += 1
    user_city = context["location"].get("city")
    user_state = context["location"].get("state")
    if user_city and product.shop.city and product.shop.city.lower() == user_city.lower():
        score += 2
    if user_state and product.shop.state and product.shop.state.lower() == user_state.lower():
        score += 1
    user_terms = context["user_terms"]
    if user_terms:
        product_terms = Counter(_tokenize(f"{product.title} {product.description}"))
        overlap = sum(
            min(count, user_terms[token])
            for token, count in product_terms.items()
            if token in user_terms
        )
        score += min(overlap, 6) * 0.5
    return score


def get_recommended_products(user, limit=12):
    if not user.is_authenticated:
        return [], {"city": None, "state": None}

    purchased_items = (
        OrderItem.objects.filter(user=user, is_ordered=True)
        .select_related("item__category", "item__shop")
    )
    favourite_items = (
        Products.objects.filter(favourite=user)
        .select_related("category", "shop")
    )

    category_counts = Counter(
        [item.item.category_id for item in purchased_items]
        + [item.category_id for item in favourite_items]
    )
    shop_counts = Counter(
        [item.item.shop_id for item in purchased_items]
        + [item.shop_id for item in favourite_items]
    )

    user_terms = Counter(
        token
        for item in purchased_items
        for token in _tokenize(f"{item.item.title} {item.item.description}")
    )
    user_terms.update(
        token
        for item in favourite_items
        for token in _tokenize(f"{item.title} {item.description}")
    )

    context = {
        "preferred_categories": set(category_counts.keys()),
        "preferred_shops": set(shop_counts.keys()),
        "category_counts": category_counts,
        "shop_counts": shop_counts,
        "purchased_products": {item.item_id for item in purchased_items},
        "location": get_user_location(user),
        "user_terms": user_terms,
    }

    candidate_products = (
        Products.objects.filter(is_active=True, available=True)
        .select_related("shop", "category")
    )

    scored_products = []
    for product in candidate_products:
        score = score_product(product, context)
        if score > 0:
            scored_products.append((score, product))

    scored_products.sort(key=lambda item: item[0], reverse=True)
    recommended_products = [product for _, product in scored_products[:limit]]

    return recommended_products, context["location"]
