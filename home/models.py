from django.db import models
from account.models import User
from foodCreate.models import Products


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="wishlist_items")
    notify_on_restock = models.BooleanField(default=True)
    notify_on_price_drop = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} - {self.product.title}"


class WishlistNotification(models.Model):
    RESTOCK = "restock"
    PRICE_DROP = "price_drop"
    NOTIFICATION_TYPES = (
        (RESTOCK, "Restock"),
        (PRICE_DROP, "Price Drop"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_notifications")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="wishlist_notifications")
    wishlist_item = models.ForeignKey(
        WishlistItem, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} - {self.notification_type}"
