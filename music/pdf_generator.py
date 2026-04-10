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


def _truncate_text(c, text, font, size, max_width):
    """Truncate text with ellipsis if it exceeds max_width."""
    if c.stringWidth(text, font, size) <= max_width:
        return text
    while len(text) > 1 and c.stringWidth(text + '...', font, size) > max_width:
        text = text[:-1]
    return text.rstrip() + '...'


def generate_license_pdf(order, profile):
    buf = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # Outer background - thin dark strip around the card
    margin = 8 * mm
    c.setFillColor(HexColor('#111111'))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Card background
    card_x = margin
    card_y = margin
    card_w = width - 2 * margin
    card_h = height - 2 * margin
    draw_rounded_rect(c, card_x, card_y, card_w, card_h, 10, fill_color=HexColor('#1a1a1a'))

    # Green border on card
    c.setStrokeColor(GREEN)
    c.setLineWidth(1.5)
    c.roundRect(card_x, card_y, card_w, card_h, 10)

    # Text margins inside the card
    pad = 18 * mm
    tx_left = card_x + pad
    tx_right = card_x + card_w - pad
    usable_w = tx_right - tx_left

    # ── Logo ──
    logo_y = height - margin - 22 * mm
    c.setFont(FONT, 26)
    c.setFillColor(GREEN)
    note_w = c.stringWidth('\u266b', FONT, 26)
    sound_w = c.stringWidth('Sound', FONT_BOLD, 28)
    free_w = c.stringWidth('Free', FONT_BOLD, 28)
    total_logo_w = note_w + 4 + sound_w + free_w
    lx = (width - total_logo_w) / 2
    c.drawString(lx, logo_y, '\u266b')
    c.setFont(FONT_BOLD, 28)
    c.setFillColor(WHITE)
    c.drawString(lx + note_w + 4, logo_y, 'Sound')
    c.setFillColor(GREEN)
    c.drawString(lx + note_w + 4 + sound_w, logo_y, 'Free')

    # ── Title ──
    y = logo_y - 14 * mm
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 20)
    c.drawCentredString(width / 2, y, 'LICENȚĂ MUZICALĂ')
    y -= 7 * mm
    c.setFont(FONT, 9)
    c.setFillColor(LIGHT)
    c.drawCentredString(width / 2, y, 'Certificat de licențiere pentru difuzare muzică în spații comerciale')

    # ── License number + QR ──
    y -= 13 * mm

    # QR Code (right)
    verify_url = f'https://www.soundfree.ro/verify/{profile.verification_token}/'
    qr_buf = generate_qr(verify_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 26 * mm
    qr_x = tx_right - qr_size
    qr_y = y - qr_size + 5 * mm
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
    c.setFont(FONT, 5.5)
    c.setFillColor(GRAY)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 3 * mm, 'Scanează pentru verificare')

    # License number (left)
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(tx_left, y, 'Nr. Licență:')
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(WHITE)
    c.drawString(tx_left, y - 6.5 * mm, order.reference)

    # ── Separator ──
    y -= 16 * mm
    c.setStrokeColor(DARK3)
    c.setLineWidth(0.5)
    c.line(tx_left, y, tx_right, y)

    # ── Company info ──
    y -= 9 * mm
    label_col = GRAY
    value_col = WHITE
    val_offset = 48 * mm
    max_val_w = usable_w - val_offset

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
            y -= 2.5 * mm
            continue
        c.setFont(FONT, 8)
        c.setFillColor(label_col)
        c.drawString(tx_left, y, label)

        val_str = str(value)
        val_font = FONT_BOLD
        val_size = 9
        # Auto-shrink and truncate to fit inside the card
        val_str = _truncate_text(c, val_str, val_font, val_size, max_val_w)
        if c.stringWidth(val_str, val_font, val_size) > max_val_w:
            val_size = 7.5
            val_str = _truncate_text(c, val_str, val_font, val_size, max_val_w)

        c.setFont(val_font, val_size)
        c.setFillColor(value_col)
        c.drawString(tx_left + val_offset, y, val_str)
        y -= 6.5 * mm

    # ── Separator ──
    y -= 3 * mm
    c.setStrokeColor(DARK3)
    c.setLineWidth(0.5)
    c.line(tx_left, y, tx_right, y)

    # ── Validity period ──
    y -= 9 * mm
    c.setFont(FONT, 8)
    c.setFillColor(label_col)
    c.drawCentredString(width / 2, y, 'Este autorizat să difuzeze muzică din')
    y -= 4.5 * mm
    c.drawCentredString(width / 2, y, 'repertoriul SoundFree pentru perioada:')

    start_str = profile.subscription_start.strftime('%d-%m-%Y') if profile.subscription_start else '-'
    end_str = profile.subscription_end.strftime('%d-%m-%Y') if profile.subscription_end else '-'

    y -= 12 * mm
    period_w = usable_w
    period_h = 14 * mm
    period_x = tx_left
    draw_rounded_rect(c, period_x, y, period_w, period_h, 5,
                       fill_color=HexColor('#0d3320'), stroke_color=GREEN)
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(GREEN)
    c.drawCentredString(width / 2, y + 4 * mm, f'{start_str}     până la     {end_str}')

    # ── Legal text ──
    y -= 14 * mm
    c.setFont(FONT, 6)
    c.setFillColor(GRAY)
    legal_lines = [
        'Prezenta licență muzicală este acordată în mod exclusiv de către SoundFree S.R.L., titular unic al drepturilor de autor și conexe, prin care se autorizează',
        'redarea repertoriului propriu SoundFree. Repertoriul este exclus oficial de la gestiunea colectivă la UCMR-ADA, CREDIDAM și UPFR.',
        'SoundFree S.R.L. exercitând gestiunea individuală a drepturilor sale și refuzând orice reprezentare sau colectare de remunerații de către orice',
        'organizație de gestiune colectivă. Licența este valabilă doar pentru locația și perioada specificate mai sus.',
    ]
    for line in legal_lines:
        c.drawCentredString(width / 2, y, line)
        y -= 3.5 * mm

    # ── Emitent ──
    y -= 7 * mm
    c.setFont(FONT, 9)
    c.setFillColor(LIGHT)
    c.drawCentredString(width / 2, y, 'Emitentul')

    y -= 6.5 * mm
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(GREEN)
    c.drawCentredString(width / 2, y, 'SOUNDFREE S.R.L.')

    y -= 5.5 * mm
    c.setFont(FONT, 7.5)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, y, 'CUI: 54416770 | J2026022358004')

    y -= 4.5 * mm
    c.drawCentredString(width / 2, y, 'Iași, România | www.soundfree.ro')

    # ── Footer watermark ──
    c.setFont(FONT, 6)
    c.setFillColor(HexColor('#2a2a2a'))
    footer_y = card_y + 5 * mm
    pattern = 'SoundFree  ·  SoundFree  ·  SoundFree  ·  SoundFree  ·  SoundFree  ·  SoundFree'
    c.drawCentredString(width / 2, footer_y, pattern)

    c.save()
    buf.seek(0)
    return buf
