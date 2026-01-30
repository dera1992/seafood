from django.db.models.signals import post_save
from django.dispatch import receiver

from account.models import ShopFollower, ShopNotification
from .models import Products


@receiver(post_save, sender=Products)
def notify_shop_followers(sender, instance, created, **kwargs):
    if not created:
        return

    followers = ShopFollower.objects.filter(shop=instance.shop).select_related("user")
    if not followers:
        return

    notifications = [
        ShopNotification(
            user=follower.user,
            shop=instance.shop,
            product=instance,
            message=f"New product from {instance.shop.name}: {instance.title}",
        )
        for follower in followers
        if follower.user_id != instance.shop.owner_id
    ]
    if notifications:
        ShopNotification.objects.bulk_create(notifications)
