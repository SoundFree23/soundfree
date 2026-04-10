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


def _wrap_text(c, text, font, size, max_width):
    """Split text into lines that fit within max_width."""
    words = str(text).split()
    lines = []
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [str(text)]


def generate_license_pdf(order, profile):
    buf = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # ── Full page dark background ──
    c.setFillColor(HexColor('#161616'))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # ── Green border - very close to page edge ──
    m = 5 * mm
    c.setStrokeColor(GREEN)
    c.setLineWidth(2)
    c.roundRect(m, m, width - 2 * m, height - 2 * m, 6)

    # Text area
    left = 22 * mm
    right = width - 22 * mm
    usable = right - left

    # ═══════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════
    y = height - 30 * mm

    # Logo
    c.setFont(FONT, 24)
    c.setFillColor(GREEN)
    note_w = c.stringWidth('\u266b', FONT, 24)
    sound_w = c.stringWidth('Sound', FONT_BOLD, 26)
    free_w = c.stringWidth('Free', FONT_BOLD, 26)
    logo_w = note_w + 3 + sound_w + free_w
    lx = (width - logo_w) / 2
    c.drawString(lx, y, '\u266b')
    c.setFont(FONT_BOLD, 26)
    c.setFillColor(WHITE)
    c.drawString(lx + note_w + 3, y, 'Sound')
    c.setFillColor(GREEN)
    c.drawString(lx + note_w + 3 + sound_w, y, 'Free')

    y -= 12 * mm
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 20)
    c.drawCentredString(width / 2, y, 'LICENȚĂ MUZICALĂ')

    y -= 7 * mm
    c.setFont(FONT, 9)
    c.setFillColor(LIGHT)
    c.drawCentredString(width / 2, y, 'Certificat de licențiere pentru difuzare muzică în spații comerciale')

    # ═══════════════════════════════════════════
    # LICENSE NUMBER + QR
    # ═══════════════════════════════════════════
    y -= 15 * mm

    # QR
    verify_url = f'https://www.soundfree.ro/verify/{profile.verification_token}/'
    qr_buf = generate_qr(verify_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 28 * mm
    qr_x = right - qr_size
    qr_y = y - qr_size + 6 * mm
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
    c.setFont(FONT, 5.5)
    c.setFillColor(GRAY)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 3 * mm, 'Scanează pentru verificare')

    # License number
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(left, y, 'Nr. Licență:')
    c.setFont(FONT_BOLD, 16)
    c.setFillColor(WHITE)
    c.drawString(left, y - 8 * mm, order.reference)

    # ═══════════════════════════════════════════
    # COMPANY INFO - label on top, value below
    # ═══════════════════════════════════════════
    y -= 25 * mm

    # Thin separator
    c.setStrokeColor(HexColor('#2a2a2a'))
    c.setLineWidth(0.5)
    c.line(left, y, right, y)
    y -= 8 * mm

    info_rows = [
        ('SoundFree licențiază', order.company_name),
        ('Care reprezintă afacerea', order.brand_name or order.company_name),
        ('Cod Unic de Înregistrare', order.company_cui),
        ('Tip activitate', BIZ_LABELS.get(order.business_type, order.business_type)),
        ('Adresa locației', order.venue_address or '-'),
        ('Suprafață', order.business_size),
    ]

    # Two-column layout for short fields, full-width for address
    col1_w = usable * 0.48
    col2_x = left + usable * 0.52

    # First pair: company + brand (side by side)
    for i in range(0, 2):
        lbl, val = info_rows[i]
        x_pos = left if i == 0 else col2_x
        c.setFont(FONT, 7)
        c.setFillColor(GRAY)
        c.drawString(x_pos, y, lbl)
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(WHITE)
        # Fit to column
        max_w = col1_w - 5 * mm
        lines = _wrap_text(c, val, FONT_BOLD, 10, max_w)
        ty = y - 5 * mm
        for line in lines[:2]:
            c.drawString(x_pos, ty, line)
            ty -= 4.5 * mm

    y -= 16 * mm

    # Second pair: CUI + Tip activitate (side by side)
    for i in range(2, 4):
        lbl, val = info_rows[i]
        x_pos = left if i == 2 else col2_x
        c.setFont(FONT, 7)
        c.setFillColor(GRAY)
        c.drawString(x_pos, y, lbl)
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(WHITE)
        c.drawString(x_pos, y - 5 * mm, str(val))

    y -= 16 * mm

    # Address - full width, wraps
    lbl, val = info_rows[4]
    c.setFont(FONT, 7)
    c.setFillColor(GRAY)
    c.drawString(left, y, lbl)
    c.setFont(FONT_BOLD, 9)
    c.setFillColor(WHITE)
    addr_lines = _wrap_text(c, val, FONT_BOLD, 9, usable)
    ty = y - 5 * mm
    for line in addr_lines[:3]:
        c.drawString(left, ty, line)
        ty -= 4 * mm
    y = ty - 2 * mm

    # Suprafata
    lbl, val = info_rows[5]
    c.setFont(FONT, 7)
    c.setFillColor(GRAY)
    c.drawString(left, y, lbl)
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(WHITE)
    c.drawString(left, y - 5 * mm, str(val))

    y -= 14 * mm

    # ═══════════════════════════════════════════
    # VALIDITY PERIOD
    # ═══════════════════════════════════════════
    c.setStrokeColor(HexColor('#2a2a2a'))
    c.setLineWidth(0.5)
    c.line(left, y, right, y)
    y -= 10 * mm

    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, y, 'Este autorizat să difuzeze muzică din repertoriul SoundFree pentru perioada:')

    start_str = profile.subscription_start.strftime('%d-%m-%Y') if profile.subscription_start else '-'
    end_str = profile.subscription_end.strftime('%d-%m-%Y') if profile.subscription_end else '-'

    y -= 13 * mm
    box_h = 15 * mm
    draw_rounded_rect(c, left, y, usable, box_h, 5,
                       fill_color=HexColor('#0d3320'), stroke_color=GREEN)
    c.setFont(FONT_BOLD, 15)
    c.setFillColor(GREEN)
    c.drawCentredString(width / 2, y + 4.5 * mm, f'{start_str}      până la      {end_str}')

    # ═══════════════════════════════════════════
    # LEGAL TEXT
    # ═══════════════════════════════════════════
    y -= 12 * mm
    c.setFont(FONT, 5.5)
    c.setFillColor(HexColor('#666666'))
    legal = (
        'Prezenta licență muzicală este acordată în mod exclusiv de către SoundFree S.R.L., titular unic al drepturilor de autor și conexe, '
        'prin care se autorizează redarea repertoriului propriu SoundFree. Repertoriul este exclus oficial de la gestiunea colectivă la UCMR-ADA, CREDIDAM și UPFR. '
        'SoundFree S.R.L. exercitând gestiunea individuală a drepturilor sale și refuzând orice reprezentare sau colectare de remunerații de către orice '
        'organizație de gestiune colectivă. Licența este valabilă doar pentru locația și perioada specificate mai sus.'
    )
    legal_lines = _wrap_text(c, legal, FONT, 5.5, usable)
    for line in legal_lines:
        c.drawString(left, y, line)
        y -= 3 * mm

    # ═══════════════════════════════════════════
    # EMITENT
    # ═══════════════════════════════════════════
    y -= 6 * mm
    c.setFont(FONT, 8)
    c.setFillColor(LIGHT)
    c.drawCentredString(width / 2, y, 'Emitentul')

    y -= 7 * mm
    c.setFont(FONT_BOLD, 13)
    c.setFillColor(GREEN)
    c.drawCentredString(width / 2, y, 'SOUNDFREE S.R.L.')

    y -= 5.5 * mm
    c.setFont(FONT, 7)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, y, 'CUI: 54416770 | J2026022358004')

    y -= 4.5 * mm
    c.drawCentredString(width / 2, y, 'Iași, România | www.soundfree.ro')

    # ── Footer watermark ──
    c.setFont(FONT, 5.5)
    c.setFillColor(HexColor('#222222'))
    c.drawCentredString(width / 2, m + 4 * mm,
                         'SoundFree · SoundFree · SoundFree · SoundFree · SoundFree · SoundFree · SoundFree')

    c.save()
    buf.seek(0)
    return buf
