"""Restored merge migration.

Migration 0008 was authored against a parent named ``0007_merge_20260402_1206``
that lived in production but was never committed to git. Its real content was
the CreateModel for Order — without it, 0010 and 0011 (which add fields to
Order) point at a model that doesn't exist in the migration state, breaking
``makemigrations``.

Production DB already has this migration recorded as applied, so the
operations below will be skipped there. On a fresh dev DB, they create the
Order table the rest of the chain expects.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0006_create_profiles_for_existing_users'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=20, unique=True, verbose_name='Referință')),
                ('plan', models.CharField(choices=[('standard', 'Standard'), ('starter', 'Starter'), ('business', 'Business'), ('enterprise', 'Enterprise')], max_length=20, verbose_name='Plan')),
                ('billing', models.CharField(choices=[('monthly', 'Lunar'), ('annual', 'Anual')], default='annual', max_length=10, verbose_name='Facturare')),
                ('business_type', models.CharField(max_length=50, verbose_name='Tip afacere')),
                ('business_size', models.CharField(max_length=50, verbose_name='Suprafață')),
                ('price_monthly', models.IntegerField(verbose_name='Preț lunar (lei)')),
                ('price_total', models.IntegerField(verbose_name='Preț total (lei)')),
                ('company_name', models.CharField(max_length=200, verbose_name='Denumire firmă')),
                ('brand_name', models.CharField(blank=True, max_length=200, verbose_name='Nume brand / locație')),
                ('company_cui', models.CharField(max_length=20, verbose_name='CUI')),
                ('company_address', models.TextField(verbose_name='Adresa firmei')),
                ('venue_address', models.TextField(blank=True, verbose_name='Adresa locației')),
                ('company_email', models.EmailField(max_length=254, verbose_name='Email firmă')),
                ('company_phone', models.CharField(max_length=30, verbose_name='Telefon firmă')),
                ('company_reg', models.CharField(blank=True, max_length=30, verbose_name='Nr. Reg. Comerț')),
                ('status', models.CharField(choices=[('pending', 'În așteptare'), ('paid', 'Plătită'), ('cancelled', 'Anulată')], default='pending', max_length=15, verbose_name='Status')),
                ('oblio_invoice', models.CharField(blank=True, max_length=100, verbose_name='Nr. factură Oblio')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='Data plată')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Utilizator')),
            ],
            options={
                'verbose_name': 'Comandă',
                'verbose_name_plural': 'Comenzi',
                'ordering': ['-created_at'],
            },
        ),
    ]
