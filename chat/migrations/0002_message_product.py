from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("foodCreate", "0004_alter_products_discount_price_alter_products_price"),
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="chat_messages",
                to="foodCreate.products",
            ),
        ),
    ]
