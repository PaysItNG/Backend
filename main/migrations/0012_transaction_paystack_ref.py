# Generated by Django 4.2 on 2025-03-11 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_alter_wallet_funds'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='paystack_ref',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
