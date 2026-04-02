# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('music', '0004_contactmessage_remove_song_artist'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_start', models.DateField(blank=True, null=True, verbose_name='Început abonament')),
                ('subscription_end', models.DateField(blank=True, null=True, verbose_name='Sfârșit abonament')),
                ('notes', models.TextField(blank=True, verbose_name='Observații')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profil utilizator',
                'verbose_name_plural': 'Profile utilizatori',
            },
        ),
    ]
