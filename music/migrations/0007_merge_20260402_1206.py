"""Stub merge migration.

Migration 0008 was authored expecting a parent named ``0007_merge_20260402_1206``
which was never committed (production DB already has it recorded as applied).
This file restores the dependency chain locally so ``check_migrations`` passes.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0006_create_profiles_for_existing_users'),
    ]

    operations = []
