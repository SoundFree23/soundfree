import io
import os
import qrcode
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'assets',
    'licenta_template.pdf'
)

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

BLACK = HexColor('#222222')
GRAY = HexColor('#444444')
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


def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#00A86B', back_color='#ffffff')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def _wrap_text(c, text, font, size, max_width):
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


def _build_overlay(order, profile):
    """Build an overlay PDF with only the dynamic fields; merged over the template."""
    buf = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    left = 25 * mm
    right = width - 25 * mm
    usable = right - left
    mid_x = left + usable / 2
    col_max_w = usable / 2 - 8 * mm

    # ── Nr. Licență (right of "Nr. Licență:" label) ──
    c.setFont(FONT_BOLD, 14)
    c.setFillColor(BLACK)
    c.drawString(58 * mm, 216 * mm, order.reference)

    # ── QR code (top-right empty square in template) ──
    verify_url = f'https://www.soundfree.ro/verify/{profile.verification_token}/'
    qr_buf = generate_qr(verify_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 26 * mm
    qr_x = right - qr_size
    qr_y = 197 * mm
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    # ── Titular licență: company name ──
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(BLACK)
    comp_lines = _wrap_text(c, order.company_name, FONT_BOLD, 11, col_max_w)
    yc = 175 * mm
    for line in comp_lines[:2]:
        c.drawString(left + 3 * mm, yc, line)
        yc -= 4.5 * mm

    # ── Cod registru value (below "Cod registru:" label) ──
    c.setFont(FONT_BOLD, 10)
    c.drawString(left + 3 * mm, 156 * mm, str(order.company_cui))

    # ── Client licențiat: brand name ──
    brand = order.brand_name or order.company_name
    c.setFont(FONT_BOLD, 11)
    brand_lines = _wrap_text(c, brand, FONT_BOLD, 11, col_max_w)
    yc = 175 * mm
    for line in brand_lines[:2]:
        c.drawString(mid_x + 3 * mm, yc, line)
        yc -= 4.5 * mm

    # ── Domeniu activitate value ──
    c.setFont(FONT_BOLD, 10)
    biz_label = BIZ_LABELS.get(order.business_type, order.business_type)
    c.drawString(mid_x + 3 * mm, 156 * mm, biz_label)

    # ── Adresă value ──
    addr_text = order.venue_address or order.company_address or '-'
    c.setFont(FONT_BOLD, 9)
    addr_lines = _wrap_text(c, addr_text, FONT_BOLD, 9, usable - 8 * mm)
    ya = 139 * mm
    for line in addr_lines[:2]:
        c.drawString(left + 3 * mm, ya, line)
        ya -= 4 * mm

    # ── Suprafață value ──
    c.setFont(FONT_BOLD, 10)
    c.drawString(left + 3 * mm, 119 * mm, str(order.business_size))

    # ── Dates on the green ribbon (white text) ──
    start_str = profile.subscription_start.strftime('%d-%m-%Y') if profile.subscription_start else '-'
    end_str = profile.subscription_end.strftime('%d-%m-%Y') if profile.subscription_end else '-'
    c.setFont(FONT_BOLD, 15)
    c.setFillColor(WHITE)
    c.drawCentredString(width / 2, 89 * mm, f'{start_str}    până la    {end_str}')

    # ── Correct CUI line in footer (template shows a wrong value) ──
    c.setFillColor(WHITE)
    c.rect(50 * mm, 19 * mm, 110 * mm, 5 * mm, fill=1, stroke=0)
    c.setFont(FONT, 9)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, 20.5 * mm, 'CUI: 54416770   |   J2026022358004')

    c.save()
    buf.seek(0)
    return buf


def generate_license_pdf(order, profile):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(
            f'License template PDF not found at {TEMPLATE_PATH}. '
            'Copy the template PDF to this location before generating licenses.'
        )

    overlay_buf = _build_overlay(order, profile)

    template_reader = PdfReader(TEMPLATE_PATH)
    overlay_reader = PdfReader(overlay_buf)

    writer = PdfWriter()
    template_page = template_reader.pages[0]
    template_page.merge_page(overlay_reader.pages[0])
    writer.add_page(template_page)

    final_buf = io.BytesIO()
    writer.write(final_buf)
    final_buf.seek(0)
    return final_buf
