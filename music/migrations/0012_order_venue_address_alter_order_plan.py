"""Restored stub for the missing migration that 0013_merge references.

The original file was deleted at some point but the migration is recorded
as applied in production's django_migrations table. Empty operations make
this a no-op everywhere.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0011_order_representative'),
    ]

    operations = []
