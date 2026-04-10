from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0009_userprofile_plain_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_type',
            field=models.CharField(choices=[('normal', 'Normal'), ('barter', 'Barter')], default='normal', max_length=10, verbose_name='Tip plată'),
        ),
    ]
