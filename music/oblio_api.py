import requests
from django.conf import settings


class OblioAPI:
    BASE_URL = 'https://www.oblio.eu/api'
    token = None

    @classmethod
    def get_token(cls):
        if cls.token:
            return cls.token
        resp = requests.post(f'{cls.BASE_URL}/authorize/token', json={
            'client_id': settings.OBLIO_EMAIL,
            'client_secret': settings.OBLIO_SECRET,
        })
        resp.raise_for_status()
        cls.token = resp.json().get('access_token')
        return cls.token

    @classmethod
    def headers(cls):
        return {'Authorization': f'Bearer {cls.get_token()}'}

    @classmethod
    def create_proforma(cls, order):
        """Create a proforma invoice in Oblio for the given order."""
        data = {
            'cif': settings.OBLIO_CIF,
            'client': {
                'cif': order.company_cui,
                'name': order.company_name,
                'rc': order.company_reg or '',
                'address': order.company_address,
                'email': order.company_email,
                'phone': order.company_phone,
            },
            'issueDate': order.created_at.strftime('%Y-%m-%d'),
            'dueDate': '',
            'seriesName': settings.OBLIO_SERIES,
            'products': [
                {
                    'name': f'Licență muzicală SoundFree - {order.business_type} ({order.business_size})',
                    'code': order.reference,
                    'description': f'Brand: {order.brand_name or "-"} | Adresa locație: {order.venue_address or "-"} | Facturare: {order.get_billing_display()}',
                    'price': order.price_total,
                    'measuringUnit': 'buc',
                    'currency': 'RON',
                    'vatName': 'Neplatitor TVA',
                    'vatPercentage': 0,
                    'vatIncluded': True,
                    'quantity': 1,
                }
            ],
            'language': 'RO',
            'precision': 2,
            'useStock': 0,
            'sendEmail': 1,
        }

        try:
            resp = requests.post(
                f'{cls.BASE_URL}/docs/proforma',
                json=data,
                headers=cls.headers(),
            )
            if resp.status_code == 401:
                cls.token = None
                resp = requests.post(
                    f'{cls.BASE_URL}/docs/proforma',
                    json=data,
                    headers=cls.headers(),
                )
            resp.raise_for_status()
            result = resp.json()
            return result.get('data', {})
        except Exception as e:
            print(f'Oblio API error: {e}')
            return None
