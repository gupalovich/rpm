# Generated by Django 4.1.7 on 2023-03-03 09:30

from django.db import migrations, models
import prm.users.validators


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_alter_user_phone_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True,
                max_length=30,
                validators=[prm.users.validators.validate_phone_number],
                verbose_name="Номер телефона",
            ),
        ),
    ]
