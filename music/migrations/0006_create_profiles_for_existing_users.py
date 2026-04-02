# Generated manually - Data migration

from django.db import migrations


def create_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('music', 'UserProfile')
    for user in User.objects.all():
        UserProfile.objects.get_or_create(user=user)


def reverse_profiles(apps, schema_editor):
    UserProfile = apps.get_model('music', 'UserProfile')
    UserProfile.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0005_userprofile'),
    ]

    operations = [
        migrations.RunPython(create_profiles, reverse_profiles),
    ]
