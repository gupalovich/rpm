# Generated by Django 4.1.7 on 2023-03-17 12:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_alter_user_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="metamask_wallet",
            field=models.CharField(
                blank=True, db_index=True, max_length=150, verbose_name="Metamask"
            ),
        ),
    ]
