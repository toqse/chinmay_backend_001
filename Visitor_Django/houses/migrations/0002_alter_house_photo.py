# Generated by Django 5.1.5 on 2025-01-22 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='house',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='house_photos/'),
        ),
    ]
