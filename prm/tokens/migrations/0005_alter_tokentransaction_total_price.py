# Generated by Django 4.1.7 on 2023-03-12 07:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tokens", "0004_remove_tokenround_progress_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tokentransaction",
            name="total_price",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10, verbose_name="Цена токенов"
            ),
        ),
    ]
