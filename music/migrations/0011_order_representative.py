from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0010_order_payment_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='company_representative',
            field=models.CharField(blank=True, max_length=200, verbose_name='Reprezentat de'),
        ),
        migrations.AddField(
            model_name='order',
            name='company_representative_role',
            field=models.CharField(blank=True, max_length=100, verbose_name='Funcția'),
        ),
    ]
