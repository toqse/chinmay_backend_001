# Generated by Django 5.1.5 on 2025-02-07 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0005_visithistory_auto_generated'),
    ]

    operations = [
        migrations.AddField(
            model_name='visithistory',
            name='review',
            field=models.TextField(blank=True, null=True),
        ),
    ]
