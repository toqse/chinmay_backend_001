# Generated by Django 5.1.5 on 2025-02-07 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0003_alter_house_ward_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='house',
            name='custom_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
