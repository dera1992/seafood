from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0006_shop_location"),
        ("foodCreate", "0004_alter_products_discount_price_alter_products_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShopFollower",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "shop",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="followers", to="account.shop"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shop_following", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ShopNotification",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_read", models.BooleanField(default=False)),
                (
                    "product",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shop_notifications", to="foodCreate.products"),
                ),
                (
                    "shop",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="account.shop"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shop_notifications", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="shopfollower",
            constraint=models.UniqueConstraint(fields=("user", "shop"), name="unique_shop_follower"),
        ),
    ]
