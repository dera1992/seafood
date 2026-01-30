from decimal import Decimal

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from foodCreate.models import Products
from home.models import WishlistItem, WishlistNotification


def _effective_price(product):
    return product.discount_price if product.discount_price is not None else product.price


@receiver(pre_save, sender=Products)
def cache_previous_product_state(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = (
        Products.objects.filter(pk=instance.pk)
        .only("stock", "price", "discount_price", "status")
        .first()
    )
    if not previous:
        return
    instance._previous_stock = previous.stock
    instance._previous_price = previous.price
    instance._previous_discount_price = previous.discount_price
    instance._previous_status = previous.status


@receiver(post_save, sender=Products)
def create_wishlist_alerts(sender, instance, created, **kwargs):
    if created:
        return
    previous_stock = getattr(instance, "_previous_stock", None)
    previous_price = getattr(instance, "_previous_price", None)
    previous_discount = getattr(instance, "_previous_discount_price", None)
    previous_status = getattr(instance, "_previous_status", None)

    if (
        previous_stock is None
        and previous_price is None
        and previous_discount is None
        and previous_status is None
    ):
        return

    restocked = False
    if previous_stock is not None:
        restocked = previous_stock <= 0 and instance.stock > 0
    elif previous_status:
        restocked = previous_status == "out_of_stock" and instance.status == "available"

    previous_effective_price = (
        previous_discount if previous_discount is not None else previous_price
    )
    current_effective_price = _effective_price(instance)

    notifications = []
    if restocked:
        for item in WishlistItem.objects.filter(
            product=instance, notify_on_restock=True
        ):
            notifications.append(
                WishlistNotification(
                    user=item.user,
                    product=instance,
                    wishlist_item=item,
                    notification_type=WishlistNotification.RESTOCK,
                    message=f"Good news! {instance.title} is back in stock.",
                )
            )

    if (
        previous_effective_price is not None
        and current_effective_price is not None
        and Decimal(current_effective_price) < Decimal(previous_effective_price)
    ):
        price_display = f"£{current_effective_price}"
        for item in WishlistItem.objects.filter(
            product=instance, notify_on_price_drop=True
        ):
            notifications.append(
                WishlistNotification(
                    user=item.user,
                    product=instance,
                    wishlist_item=item,
                    notification_type=WishlistNotification.PRICE_DROP,
                    message=f"Price drop alert: {instance.title} is now {price_display}.",
                )
            )

    if notifications:
        WishlistNotification.objects.bulk_create(notifications)
