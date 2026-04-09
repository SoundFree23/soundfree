import io
import os
import qrcode
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings


# Register DejaVu font for Romanian diacritics support
try:
    import reportlab
    font_dir = os.path.join(os.path.dirname(reportlab.__file__), 'fonts')
    dejavu_path = os.path.join(font_dir, 'DejaVuSans.ttf')
    dejavu_bold_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
    if not os.path.exists(dejavu_path):
        # Try system paths
        for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                   'C:/Windows/Fonts/arial.ttf']:
            if os.path.exists(p):
                dejavu_path = p
                dejavu_bold_path = p.replace('Sans.ttf', 'Sans-Bold.ttf').replace('arial.ttf', 'arialbd.ttf')
                break
    if os.path.exists(dejavu_path):
        pdfmetrics.registerFont(TTFont('DejaVu', dejavu_path))
    if os.path.exists(dejavu_bold_path):
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', dejavu_bold_path))
    FONT = 'DejaVu'
    FONT_BOLD = 'DejaVu-Bold'
except Exception:
    FONT = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'

GREEN = HexColor('#1db954')
DARK = HexColor('#121212')
DARK2 = HexColor('#1a1a1a')
DARK3 = HexColor('#222222')
GRAY = HexColor('#888888')
LIGHT = HexColor('#e0e0e0')
WHITE = white

BIZ_LABELS = {
    'cafenea': 'Cafenea / Cofetărie',
    'restaurant': 'Restaurant / Pizzerie',
    'bar': 'Bar / Pub',
    'club': 'Club / Discotecă',
    'hotel': 'Hotel / Pensiune',
    'salon': 'Salon / Spa',
    'retail': 'Magazine / Retail',
    'birou': 'Birou / Coworking',
    'cabinet': 'Cabinet / Clinică',
    'gym': 'Gym / Fitness',
}


def generate_qr(url, size=150):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1db954', back_color='#121212')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None):
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - r, y, x + w, y + r, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w, y + h - r, x + w - r, y + h, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x + r, y + h, x, y + h - r, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y + r, x + r, y, 90)
    p.close()
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.drawPath(p, fill=1 if fill_color else 0, stroke=1 if stroke_color else 0)
    else:
        c.drawPath(p, fill=1 if fill_color else 0, stroke=0)


def generate_license_pdf(order, profile):
    buf = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # Background
    c.setFillColor(DARK)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Border
    margin = 15 * mm
    c.setStrokeColor(GREEN)
    c.setLineWidth(2)
    c.roundRect(margin, margin, width - 2 * margin, height - 2 * margin, 10)

    # Inner border
    c.setStrokeColor(DARK3)
    c.setLineWidth(0.5)
    c.roundRect(margin + 5, margin + 5, width - 2 * margin - 10, height - 2 * margin - 10, 8)

    # Logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'Logo.png')
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        logo_w = 60 * mm
        logo_h = 24 * mm
        c.drawImage(logo, (width - logo_w) / 2, height - margin - 45 * mm, width=logo_w, height=logo_h, mask='auto')

    # Title
    y = height - margin - 55 * mm
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 22)
    c.drawCentredString(width / 2, y, 'LICENȚĂ MUZICALĂ')
    y -= 8 * mm
    c.setFont(FONT, 11)
    c.setFillColor(LIGHT)
    c.drawCentredString(width / 2, y, 'Certificat de licențiere pentru difuzare muzică în spații comerciale')

    # License number + QR code
    y -= 15 * mm

    # QR Code (right side)
    verify_url = f'https://www.soundfree.ro/verify/{profile.verification_token}/'
    qr_buf = generate_qr(verify_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 30 * mm
    qr_x = width - margin - qr_size - 15 * mm
    qr_y = y - qr_size + 5 * mm
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
    c.setFont(FONT, 6)
    c.setFillColor(GRAY)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 4 * mm, 'Scanează pentru verificare')

    # License number (left side)
    c.setFont(FONT, 9)
    c.setFillColor(GRAY)
    left_x = margin + 20 * mm
    c.drawString(left_x, y, 'Nr. Licență:')
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(WHITE)
    c.drawString(left_x, y - 7 * mm, order.reference)

    # Separator
    y -= 20 * mm
    c.setStrokeColor(DARK3)
    c.setLineWidth(1)
    c.line(margin + 15 * mm, y, width - margin - 15 * mm, y)

    # Company info section
    y -= 12 * mm
    info_x = margin + 20 * mm
    label_color = GRAY
    value_color = WHITE

    rows = [
        ('SoundFree licențiază:', order.company_name),
        ('Care reprezintă afacerea:', order.brand_name or order.company_name),
        ('', ''),
        ('Cod Unic de Înregistrare:', order.company_cui),
        ('Tip activitate:', BIZ_LABELS.get(order.business_type, order.business_type)),
        ('Adresa locației:', order.venue_address or '-'),
        ('Suprafață:', order.business_size),
    ]

    for label, value in rows:
        if not label and not value:
            y -= 4 * mm
            continue
        c.setFont(FONT, 9)
        c.setFillColor(label_color)
        c.drawString(info_x, y, label)
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(value_color)
        # Handle long values
        if len(str(value)) > 50:
            c.setFont(FONT_BOLD, 8)
        c.drawString(info_x + 55 * mm, y, str(value))
        y -= 7 * mm

    # Separator
    y -= 5 * mm
    c.setStrokeColor(DARK3)
    c.line(margin + 15 * mm, y, width - margin - 15 * mm, y)

    # Validity period
    y -= 12 * mm
    c.setFont(FONT, 9)
    c.setFillColor(label_color)
    c.drawString(info_x, y, 'Este autorizat să difuzeze muzică din')
    y -= 6 * mm
    c.drawString(info_x, y, 'repertoriul SoundFree pentru perioada:')

    start_str = profile.subscription_start.strftime('%d-%m-%Y') if profile.subscription_start else '-'
    end_str = profile.subscription_end.strftime('%d-%m-%Y') if profile.subscription_end else '-'

    y -= 10 * mm
    # Green period box
    period_w = 120 * mm
    period_h = 12 * mm
    period_x = (width - period_w) / 2
    draw_rounded_rect(c, period_x, y - 2 * mm, period_w, period_h, 3, fill_color=HexColor('#0d3320'), stroke_color=GREEN)
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(GREEN)
    c.drawCentredString(width / 2, y + 1 * mm, f'{start_str}     până la     {end_str}')

    # Legal text
    y -= 22 * mm
    c.setFont(FONT, 6.5)
    c.setFillColor(GRAY)
    legal_lines = [
        'Prezenta licență muzicală este acordată în mod exclusiv de către SoundFree S.R.L., titular unic al drepturilor de autor și conexe, prin care se autorizează',
        'redarea repertoriului propriu SoundFree. Repertoriul este exclus oficial de la gestiunea colectivă la UCMR-ADA, CREDIDAM și UPFR.',
        'SoundFree S.R.L. exercitând gestiunea individuală a drepturilor sale și refuzând orice reprezentare sau colectare de remunerații de către orice',
        'organizație de gestiune colectivă. Licența este valabilă doar pentru locația și perioada specificate mai sus.',
    ]
    for line in legal_lines:
        c.drawCentredString(width / 2, y, line)
        y -= 4 * mm

    # Emitent section
    y -= 10 * mm
    c.setFont(FONT, 10)
    c.setFillColor(LIGHT)
    c.drawCentredString(width / 2, y, 'Emitentul')

    y -= 8 * mm
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(GREEN)
    c.drawCentredString(width / 2, y, 'SOUNDFREE S.R.L.')

    y -= 6 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, y, 'CUI: 54416770 | J2026022358004')

    y -= 5 * mm
    c.drawCentredString(width / 2, y, 'Iași, România | www.soundfree.ro')

    # Footer with SoundFree watermark pattern
    c.setFont(FONT, 7)
    c.setFillColor(HexColor('#333333'))
    footer_y = margin + 8 * mm
    pattern = 'SoundFree   ·   SoundFree   ·   SoundFree   ·   SoundFree   ·   SoundFree   ·   SoundFree'
    c.drawCentredString(width / 2, footer_y, pattern)

    c.save()
    buf.seek(0)
    return buf
