# Generated by Django 4.2 on 2025-03-14 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='card_holder_ref',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
