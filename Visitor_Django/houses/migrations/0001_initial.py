# Generated by Django 5.1.5 on 2025-01-22 03:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='House',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('house_number', models.CharField(max_length=50)),
                ('ward_number', models.IntegerField()),
                ('resident_name', models.CharField(max_length=100)),
                ('mobile_number', models.CharField(max_length=15)),
                ('photo', models.ImageField(upload_to='house_photos/')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('address', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('panchayath', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('panchayath', 'house_number')},
            },
        ),
        migrations.CreateModel(
            name='VisitHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visit_date', models.DateField()),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('visited', models.BooleanField(default=False)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visits', to='houses.house')),
            ],
            options={
                'ordering': ['visit_date'],
            },
        ),
    ]
