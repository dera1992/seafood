from django import template
from order.models import Order
from home.models import WishlistItem

register = template.Library()


@register.filter
def cart_item_count(user):
    if user.is_authenticated:
        qs = Order.objects.filter(user=user, is_ordered=False)
        if qs.exists():
            return qs[0].items.count()
    return 0

@register.filter
def wish_item_count(user):
    if user.is_authenticated:
        qs = WishlistItem.objects.filter(user=user)
        if qs.exists():
            return qs.count()
    return 0
