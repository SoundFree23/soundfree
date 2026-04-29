from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from music.models import UserProfile, Order


class Command(BaseCommand):
    help = 'Send renewal reminders and proforma invoices 10 days before subscription expiry'

    def handle(self, *args, **options):
        target_date = date.today() + timedelta(days=10)
        expiring = UserProfile.objects.filter(
            subscription_end=target_date,
        ).select_related('user')

        count = 0
        for profile in expiring:
            user = profile.user
            if user.is_staff:
                continue

            # Find last paid order for this user
            last_order = Order.objects.filter(
                user=user, status='paid'
            ).order_by('-created_at').first()

            if not last_order:
                continue

            # Create renewal order (pending)
            new_order = Order.objects.create(
                user=user,
                plan='standard',
                billing=last_order.billing,
                business_type=last_order.business_type,
                business_size=last_order.business_size,
                price_monthly=last_order.price_monthly,
                price_total=last_order.price_total,
                company_name=last_order.company_name,
                brand_name=last_order.brand_name,
                company_cui=last_order.company_cui,
                company_address=last_order.company_address,
                venue_address=last_order.venue_address,
                company_email=last_order.company_email,
                company_phone=last_order.company_phone,
                company_reg=last_order.company_reg,
                status='pending',
            )

            # Generate proforma in Oblio
            try:
                from music.oblio_api import OblioAPI
                result = OblioAPI.create_proforma(new_order)
                if result and result.get('seriesName'):
                    new_order.oblio_invoice = f"{result.get('seriesName')}{result.get('number', '')}"
                    new_order.save(update_fields=['oblio_invoice'])
            except Exception as e:
                self.stderr.write(f'Oblio error for {user.username}: {e}')

            # Send reminder email
            try:
                send_mail(
                    subject='[SoundFree] Licența ta expiră în 10 zile — Reînnoire',
                    message=(
                        f'Bună ziua,\n\n'
                        f'Licența dumneavoastră muzicală SoundFree pentru "{last_order.brand_name or last_order.company_name}" '
                        f'expiră pe {profile.subscription_end.strftime("%d.%m.%Y")}.\n\n'
                        f'Pentru a continua să difuzați muzică legal, vă rugăm să efectuați plata de reînnoire:\n\n'
                        f'Detalii reînnoire:\n'
                        f'- Referință: {new_order.reference}\n'
                        f'- Firmă: {new_order.company_name}\n'
                        f'- Brand: {new_order.brand_name or "-"}\n'
                        f'- Adresa locație: {new_order.venue_address}\n'
                        f'- Valoare: {new_order.price_total} lei ({new_order.get_billing_display()})\n\n'
                        f'Date pentru plata prin transfer bancar:\n'
                        f'- Titular: SOUNDFREE SRL\n'
                        f'- IBAN: RO57RZBR0000060030141147\n'
                        f'- Banca: Raiffeisen Bank\n'
                        f'- Referință plată: {new_order.reference}\n\n'
                        f'Proforma a fost trimisă și pe email de către sistemul de facturare.\n\n'
                        f'♫ SoundFree\n'
                        f'Muzică licențiată pentru afacerea ta\n'
                        f'www.soundfree.ro | office@soundfree.ro | 0733 272 263'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[last_order.company_email],
                    fail_silently=True,
                )
            except Exception as e:
                self.stderr.write(f'Email error for {user.username}: {e}')

            count += 1
            self.stdout.write(f'Reminder sent: {user.username} ({last_order.company_email}) - expires {profile.subscription_end}')

        self.stdout.write(self.style.SUCCESS(f'Done. {count} reminders sent.'))
