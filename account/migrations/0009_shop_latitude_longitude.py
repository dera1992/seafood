from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0008_shop_currency_unit_shopintegration"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="shop",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
            ),
        ),
    ]
