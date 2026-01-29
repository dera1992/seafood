from django.db import migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0005_shop_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="location",
            field=django.contrib.gis.db.models.fields.PointField(
                blank=True,
                geography=True,
                null=True,
                srid=4326,
            ),
        ),
        migrations.RemoveField(
            model_name="shop",
            name="latitude",
        ),
        migrations.RemoveField(
            model_name="shop",
            name="longitude",
        ),
    ]
