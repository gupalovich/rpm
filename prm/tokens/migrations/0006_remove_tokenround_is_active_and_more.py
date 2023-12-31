# Generated by Django 4.1.7 on 2023-03-13 17:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tokens", "0005_alter_tokentransaction_total_price"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tokenround",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="tokenround",
            name="is_complete",
        ),
        migrations.AddField(
            model_name="tokentransaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Failed", "Failed"),
                    ("Success", "Success"),
                ],
                default="Pending",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
    ]
