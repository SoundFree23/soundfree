"""Restored stub for another untracked merge migration referenced by 0015.

The original file was created on production but never committed.
0015_merge_20260421_1718 lists it as a parent. Empty operations make
this a no-op everywhere — production already has it applied.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0011_order_representative'),
    ]

    operations = []
