# Generated manually
import uuid
from django.db import migrations, models


def populate_tokens(apps, schema_editor):
    UserProfile = apps.get_model('music', 'UserProfile')
    for profile in UserProfile.objects.all():
        if not profile.verification_token:
            profile.verification_token = uuid.uuid4()
            profile.save(update_fields=['verification_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0007_merge_20260402_1206'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=False, verbose_name='Token verificare'),
            preserve_default=False,
        ),
        migrations.RunPython(populate_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='userprofile',
            name='verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Token verificare'),
        ),
    ]
