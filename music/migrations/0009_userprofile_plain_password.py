from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0008_userprofile_verification_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='plain_password',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Parolă (text clar)'),
        ),
    ]
