from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("budget", "0003_shoppinglistitem_name_optional_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shoppinglistitem",
            name="name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
