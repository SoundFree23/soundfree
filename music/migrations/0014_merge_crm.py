"""Merge migration that joins the CRM branch with the production branch.

Production has migration 0013_merge_20260410_1144 already applied.
The dev branch added 0012_contactmessage_phone_lead with the Lead model.
This stub closes the diamond so the graph has a single tip again.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0012_contactmessage_phone_lead'),
        ('music', '0013_merge_20260410_1144'),
    ]

    operations = []
