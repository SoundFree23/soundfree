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
from reportlab.graphics import renderPDF
from django.conf import settings

# Try to import svglib for SVG template rendering
try:
    from svglib.svglib import svg2rlg
    HAS_SVGLIB = True
except ImportError:
    HAS_SVGLIB = False

# Register DejaVu font for Romanian diacritics support
try:
    import reportlab
    font_dir = os.path.join(os.path.dirname(reportlab.__file__), 'fonts')
    dejavu_path = os.path.join(font_dir, 'DejaVuSans.ttf')
    dejavu_bold_path = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
    if not os.path.exists(dejavu_path):
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

GREEN = HexColor('#00A86B')
DARK_GREEN = HexColor('#006B45')
LIGHT_GREEN = HexColor('#e0f5eb')
BLACK = HexColor('#222222')
GRAY = HexColor('#444444')
LIGHT_GRAY = HexColor('#888888')
WHITE = white

BIZ_LABELS = {
    'cafenea': 'Cafenea / Cofetarie',
    'restaurant': 'Restaurant / Pizzerie',
    'bar': 'Bar / Pub',
    'club': 'Club / Discoteca',
    'hotel': 'Hotel / Pensiune',
    'salon': 'Salon / Spa',
    'retail': 'Magazine / Retail',
    'birou': 'Birou / Coworking',
    'cabinet': 'Cabinet / Clinica',
    'gym': 'Gym / Fitness',
}


def generate_qr(url, size=150):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#00A86B', back_color='#ffffff')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None, line_width=1):
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
        c.setLineWidth(line_width)
        c.drawPath(p, fill=1 if fill_color else 0, stroke=1)
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


def _draw_decorations(c, width, height):
    """Draw all decorative elements: treble clef, staff lines, music notes."""
    # Treble clef watermark (top-left, large and subtle)
    c.saveState()
    c.setFillColor(HexColor('#e8f5e9'))
    c.setFont(FONT, 140)
    # Use standard music symbols that DejaVu supports
    c.drawString(5 * mm, height - 85 * mm, '\u266b')
    c.setFont(FONT, 90)
    c.drawString(12 * mm, height - 55 * mm, '\u266b')
    c.setFont(FONT, 60)
    c.drawString(8 * mm, height - 30 * mm, '\u266a')
    c.restoreState()

    # Wavy staff lines behind header
    c.saveState()
    c.setStrokeColor(HexColor('#00A86B'))
    c.setLineWidth(0.6)
    left_start = 35 * mm
    right_end = width - 15 * mm
    base_y = height - 42 * mm
    for i in range(5):
        line_y = base_y - i * 2.2 * mm
        p = c.beginPath()
        p.moveTo(left_start, line_y)
        # Wavy curve
        p.curveTo(left_start + 40 * mm, line_y + 3 * mm,
                  width / 2 - 20 * mm, line_y - 2 * mm,
                  width / 2, line_y + 1 * mm)
        p.curveTo(width / 2 + 20 * mm, line_y + 4 * mm,
                  right_end - 40 * mm, line_y - 1 * mm,
                  right_end, line_y + 2 * mm)
        c.setLineWidth(0.5)
        c.setStrokeAlpha(0.12)
        c.drawPath(p, fill=0, stroke=1)
    c.restoreState()

    # Music notes scattered around header area
    c.saveState()
    c.setFillColor(HexColor('#00A86B'))
    notes_data = [
        (55 * mm, height - 30 * mm, 20, '\u266b'),
        (75 * mm, height - 36 * mm, 16, '\u266a'),
        (95 * mm, height - 28 * mm, 18, '\u266b'),
        (130 * mm, height - 34 * mm, 15, '\u266a'),
        (150 * mm, height - 29 * mm, 20, '\u266b'),
        (170 * mm, height - 35 * mm, 16, '\u266a'),
        (190 * mm, height - 30 * mm, 18, '\u266b'),
    ]
    for nx, ny, ns, nc in notes_data:
        c.saveState()
        c.setFillAlpha(0.10)
        c.setFont(FONT, ns)
        c.drawString(nx, ny, nc)
        c.restoreState()
    c.restoreState()

    # Music notes decoration line (between license number and info box)
    c.saveState()
    note_y = height - 82 * mm
    note_chars = ['\u266b', '\u266a'] * 8
    nx = 25 * mm
    for i, nc in enumerate(note_chars):
        c.saveState()
        c.setFillColor(HexColor('#cccccc'))
        c.setFillAlpha(0.5)
        size = 12 if i % 2 == 0 else 10
        c.setFont(FONT, size)
        c.drawString(nx, note_y + (1 if i % 2 == 0 else -1) * mm, nc)
        c.restoreState()
        nx += 8 * mm
        if nx > width / 2 + 40 * mm:
            break
    c.restoreState()

    # Subtle wavy staff under the notes decoration
    c.saveState()
    c.setStrokeColor(HexColor('#00A86B'))
    staff_y = note_y - 3 * mm
    for i in range(3):
        sy = staff_y - i * 1.5 * mm
        p = c.beginPath()
        p.moveTo(25 * mm, sy)
        p.curveTo(60 * mm, sy + 1.5 * mm, 100 * mm, sy - 1 * mm, 140 * mm, sy + 0.5 * mm)
        c.setLineWidth(0.4)
        c.setStrokeAlpha(0.07)
        c.drawPath(p, fill=0, stroke=1)
    c.restoreState()


def generate_license_pdf(order, profile):
    buf = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # ── White background ──
    c.setFillColor(WHITE)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Page margins
    left = 25 * mm
    right = width - 25 * mm
    usable = right - left

    # ── Draw all decorative elements ──
    _draw_decorations(c, width, height)

    # ═══════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════
    y = height - 28 * mm

    # Logo: ♫ SoundFree
    c.setFont(FONT, 20)
    c.setFillColor(GREEN)
    note_w = c.stringWidth('\u266b', FONT, 20)
    sound_w = c.stringWidth('Sound', FONT_BOLD, 22)
    free_w = c.stringWidth('Free', FONT_BOLD, 22)
    logo_w = note_w + 3 + sound_w + free_w
    lx = (width - logo_w) / 2
    c.drawString(lx, y, '\u266b')
    c.setFont(FONT_BOLD, 22)
    c.setFillColor(BLACK)
    c.drawString(lx + note_w + 3, y, 'Sound')
    c.setFillColor(GREEN)
    c.drawString(lx + note_w + 3 + sound_w, y, 'Free')

    # Title
    y -= 12 * mm
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 24)
    c.drawCentredString(width / 2, y, 'LICENTA MUZICALA')

    y -= 7 * mm
    c.setFont(FONT, 9)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, y, 'Certificat de licentiere pentru difuzare muzica in spatii comerciale')

    # Green separator line
    y -= 6 * mm
    c.setStrokeColor(GREEN)
    c.setLineWidth(1.5)
    c.line(left, y, right, y)

    # ═══════════════════════════════════════════
    # LICENSE NUMBER + QR CODE
    # ═══════════════════════════════════════════
    y -= 14 * mm

    # License number
    c.setFont(FONT, 9)
    c.setFillColor(GRAY)
    c.drawString(left, y, 'Nr. Licenta:')
    nr_x = left + c.stringWidth('Nr. Licenta: ', FONT, 9)
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(BLACK)
    c.drawString(nr_x, y, order.reference)

    # QR Code with gray border
    verify_url = f'https://www.soundfree.ro/verify/{profile.verification_token}/'
    qr_buf = generate_qr(verify_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 28 * mm
    qr_x = right - qr_size
    qr_y = y - qr_size + 8 * mm
    # Gray border around QR
    qr_pad = 1.5 * mm
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(0.5)
    c.rect(qr_x - qr_pad, qr_y - qr_pad, qr_size + 2 * qr_pad, qr_size + 2 * qr_pad, fill=0, stroke=1)
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    # ═══════════════════════════════════════════
    # COMPANY INFO BOX
    # ═══════════════════════════════════════════
    y -= 30 * mm

    box_top = y + 4 * mm
    box_h = 72 * mm
    mid_x = left + usable / 2
    col_max_w = usable / 2 - 8 * mm

    # Box border
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(0.5)
    c.rect(left, box_top - box_h, usable, box_h, fill=0, stroke=1)

    # Vertical divider (top section only)
    c.line(mid_x, box_top, mid_x, box_top - 38 * mm)
    # Horizontal divider
    c.line(left, box_top - 38 * mm, right, box_top - 38 * mm)

    # ── LEFT: Titular licenta ──
    col_y = box_top - 5 * mm
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(GREEN)
    c.drawString(left + 3 * mm, col_y, 'Titular licenta')

    col_y -= 5 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(left + 3 * mm, col_y, 'Nume firma:')
    col_y -= 5 * mm
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(BLACK)
    comp_lines = _wrap_text(c, order.company_name, FONT_BOLD, 11, col_max_w)
    for line in comp_lines[:2]:
        c.drawString(left + 3 * mm, col_y, line)
        col_y -= 4.5 * mm

    col_y -= 1 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(left + 3 * mm, col_y, 'Cod registru:')
    col_y -= 5 * mm
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(BLACK)
    c.drawString(left + 3 * mm, col_y, str(order.company_cui))

    # ── RIGHT: Client licentiat ──
    col_y = box_top - 5 * mm
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(GREEN)
    c.drawString(mid_x + 3 * mm, col_y, 'Client licentiat')

    col_y -= 5 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(mid_x + 3 * mm, col_y, 'Nume client:')
    col_y -= 5 * mm
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(BLACK)
    brand = order.brand_name or order.company_name
    brand_lines = _wrap_text(c, brand, FONT_BOLD, 11, col_max_w)
    for line in brand_lines[:2]:
        c.drawString(mid_x + 3 * mm, col_y, line)
        col_y -= 4.5 * mm

    col_y -= 1 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(mid_x + 3 * mm, col_y, 'Colectie:')
    col_y -= 5 * mm
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(BLACK)
    c.drawString(mid_x + 3 * mm, col_y, BIZ_LABELS.get(order.business_type, order.business_type))

    # ── ADDRESS (full width, below divider) ──
    addr_y = box_top - 38 * mm - 5 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(left + 3 * mm, addr_y, 'Adresa:')
    addr_y -= 5 * mm
    c.setFont(FONT_BOLD, 9)
    c.setFillColor(BLACK)
    addr_text = order.venue_address or order.company_address or '-'
    addr_lines = _wrap_text(c, addr_text, FONT_BOLD, 9, usable - 8 * mm)
    for line in addr_lines[:3]:
        c.drawString(left + 3 * mm, addr_y, line)
        addr_y -= 4 * mm

    # ── SURFACE ──
    addr_y -= 1 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawString(left + 3 * mm, addr_y, 'Suprafata:')
    addr_y -= 5 * mm
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(BLACK)
    c.drawString(left + 3 * mm, addr_y, str(order.business_size))

    # ═══════════════════════════════════════════
    # VALIDITY PERIOD - Green ribbon
    # ═══════════════════════════════════════════
    y = box_top - box_h - 10 * mm

    # "LICENTA VALABILA" badge
    c.setFont(FONT_BOLD, 8)
    lv_text = 'LICENTA VALABILA'
    lv_w = c.stringWidth(lv_text, FONT_BOLD, 8)
    lv_pad = 4 * mm
    draw_rounded_rect(c, (width - lv_w) / 2 - lv_pad, y + 1 * mm,
                       lv_w + 2 * lv_pad, 5.5 * mm, 3,
                       fill_color=LIGHT_GREEN, stroke_color=GREEN, line_width=0.5)
    c.setFillColor(DARK_GREEN)
    c.drawCentredString(width / 2, y + 2.5 * mm, lv_text)

    # Green ribbon
    y -= 7 * mm
    ribbon_h = 15 * mm
    draw_rounded_rect(c, left - 5 * mm, y, usable + 10 * mm, ribbon_h, 4,
                       fill_color=DARK_GREEN)

    # Ribbon fold effects
    c.setFillColor(HexColor('#004D32'))
    p = c.beginPath()
    p.moveTo(left - 5 * mm, y + ribbon_h)
    p.lineTo(left - 5 * mm + 4 * mm, y + ribbon_h)
    p.lineTo(left - 5 * mm, y + ribbon_h - 4 * mm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(right + 5 * mm, y + ribbon_h)
    p.lineTo(right + 5 * mm - 4 * mm, y + ribbon_h)
    p.lineTo(right + 5 * mm, y + ribbon_h - 4 * mm)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Dates
    start_str = profile.subscription_start.strftime('%d-%m-%Y') if profile.subscription_start else '-'
    end_str = profile.subscription_end.strftime('%d-%m-%Y') if profile.subscription_end else '-'

    c.setFont(FONT_BOLD, 16)
    c.setFillColor(WHITE)
    c.drawCentredString(width / 2, y + 4 * mm, f'{start_str}      pana la      {end_str}')

    # ═══════════════════════════════════════════
    # LEGAL TEXT
    # ═══════════════════════════════════════════
    y -= 14 * mm
    c.setFont(FONT, 7)
    c.setFillColor(GRAY)
    legal = (
        'Prezenta licenta muzicala este acordata in mod exclusiv de catre SoundFree S.R.L. (CUI 54416770), '
        'titular unic al drepturilor de autor si conexe, prin care se autorizeaza redarea repertoriului propriu SoundFree. '
        'Repertoriul este compus si licentiat integral de echipa SoundFree, fara drepturi terte. '
        'In temeiul Legii nr. 8/1996 privind dreptul de autor si drepturile conexe, '
        'SoundFree S.R.L. exercita gestiunea individuala a drepturilor sale si refuza orice reprezentare sau '
        'colectare de remuneratii de catre orice organizatie de gestiune colectiva (UCMR-ADA, CREDIDAM, UPFR). '
        'Licenta este valabila doar pentru locatia si perioada specificate. '
        'Reproducerea neautorizata atrage raspundere legala.'
    )
    legal_lines = _wrap_text(c, legal, FONT, 7, usable)
    for line in legal_lines:
        c.drawString(left, y, line)
        y -= 3.3 * mm

    # ═══════════════════════════════════════════
    # SEPARATOR
    # ═══════════════════════════════════════════
    y -= 5 * mm
    c.setStrokeColor(HexColor('#e0e0e0'))
    c.setLineWidth(0.5)
    c.line(left + 30 * mm, y, right - 30 * mm, y)

    # ═══════════════════════════════════════════
    # EMITENT / FOOTER
    # ═══════════════════════════════════════════
    y -= 10 * mm

    # Logo: ♫ SoundFree
    c.setFont(FONT, 14)
    c.setFillColor(GREEN)
    nw = c.stringWidth('\u266b', FONT, 14)
    sw = c.stringWidth('Sound', FONT_BOLD, 16)
    fw = c.stringWidth('Free', FONT_BOLD, 16)
    lw = nw + 2 + sw + fw
    fx = (width - lw) / 2
    c.drawString(fx, y, '\u266b')
    c.setFont(FONT_BOLD, 16)
    c.setFillColor(BLACK)
    c.drawString(fx + nw + 2, y, 'Sound')
    c.setFillColor(GREEN)
    c.drawString(fx + nw + 2 + sw, y, 'Free')

    y -= 6 * mm
    c.setFont(FONT, 8)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, y, 'CUI: 54416770')

    y -= 4.5 * mm
    c.drawCentredString(width / 2, y, 'Nr. inregistrare: J2026022358004')

    y -= 4.5 * mm
    c.drawCentredString(width / 2, y, 'www.soundfree.ro')

    c.save()
    buf.seek(0)
    return buf
