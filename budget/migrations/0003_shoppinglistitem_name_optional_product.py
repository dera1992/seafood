from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("budget", "0002_budget_templates"),
    ]

    operations = [
        migrations.AddField(
            model_name="shoppinglistitem",
            name="name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="shoppinglistitem",
            name="product",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to="foodCreate.products"),
        ),
        migrations.AlterUniqueTogether(
            name="shoppinglistitem",
            unique_together={("budget", "product", "name")},
        ),
    ]
