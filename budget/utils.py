from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from foodCreate.models import Products


def get_effective_price(product: Products) -> Decimal:
    if product.discount_price:
        return product.discount_price
    return product.price


def build_price_predictions(items):
    predictions = []
    today = timezone.localdate()
    for item in items:
        product = item.product
        if not product:
            continue
        if product.expires_on and product.expires_on <= today + timedelta(days=7):
            message = 'Discount ending soon — price may rise.'
        elif product.discount_price:
            message = 'Discount available — consider buying now.'
        else:
            message = 'Price appears stable based on available data.'
        predictions.append({
            'product': product,
            'message': message,
        })
    return predictions


def build_savings_suggestions(items, remaining_budget):
    suggestions = defaultdict(list)
    if remaining_budget <= 0:
        return suggestions

    for item in items:
        if not item.product:
            continue
        category = item.product.category
        current_price = get_effective_price(item.product)
        alternatives = Products.objects.filter(category=category)
        alternatives = alternatives.exclude(id=item.product_id)
        alternatives = alternatives.filter(price__lte=current_price)
        alternatives = alternatives.order_by('price')[:3]
        suggestions[item.product] = [product for product in alternatives if get_effective_price(product) <= remaining_budget]
    return suggestions
