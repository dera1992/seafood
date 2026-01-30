from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("account", "0006_shop_location"),
        ("foodCreate", "0004_alter_products_discount_price_alter_products_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="WishlistItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("notify_on_restock", models.BooleanField(default=True)),
                ("notify_on_price_drop", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist_items",
                        to="foodCreate.Products",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist_items",
                        to="account.User",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "unique_together": {("user", "product")},
            },
        ),
        migrations.CreateModel(
            name="WishlistNotification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "notification_type",
                    models.CharField(
                        choices=[("restock", "Restock"), ("price_drop", "Price Drop")],
                        max_length=20,
                    ),
                ),
                ("message", models.CharField(max_length=255)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist_notifications",
                        to="foodCreate.Products",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist_notifications",
                        to="account.User",
                    ),
                ),
                (
                    "wishlist_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="home.WishlistItem",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
