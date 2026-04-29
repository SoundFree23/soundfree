"""One-shot script: generate PWA icons from static/Logo.png.

Run once after editing the source logo. Outputs land in static/pwa/.

Strategy: place the full SoundFree banner logo onto a square dark canvas with
breathing room. Maskable variants get extra padding so Android's adaptive-icon
mask doesn't clip the logo edges.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'static' / 'Logo.png'
OUT = ROOT / 'static' / 'pwa'
OUT.mkdir(parents=True, exist_ok=True)

BG = (18, 18, 18, 255)   # site dark background (#121212)


def fit_logo_to_square(size: int, pad_ratio: float) -> Image.Image:
    """Place the full banner logo, scaled to fit within (1 - 2*pad_ratio) of the square width, centered."""
    canvas = Image.new('RGBA', (size, size), BG)
    logo = Image.open(SRC).convert('RGBA')

    safe_w = int(size * (1 - 2 * pad_ratio))
    lw, lh = logo.size
    scale = safe_w / lw
    new_size = (safe_w, max(1, int(lh * scale)))
    logo = logo.resize(new_size, Image.LANCZOS)

    offset_x = (size - new_size[0]) // 2
    offset_y = (size - new_size[1]) // 2
    canvas.paste(logo, (offset_x, offset_y), logo)
    return canvas


def make_icon(size: int, maskable: bool = False) -> Image.Image:
    pad = 0.18 if maskable else 0.08
    return fit_logo_to_square(size, pad)


SIZES = [
    ('icon-192.png',           192, False),
    ('icon-512.png',           512, False),
    ('icon-maskable-192.png',  192, True),
    ('icon-maskable-512.png',  512, True),
    ('apple-touch-icon.png',   180, False),
    ('favicon-32.png',          32, False),
    ('favicon-16.png',          16, False),
]

for name, size, maskable in SIZES:
    icon = make_icon(size, maskable=maskable)
    icon.save(OUT / name, 'PNG', optimize=True)
    print(f'  wrote {name}  ({size}x{size}{" maskable" if maskable else ""})')

print(f'\nDone. {len(SIZES)} icons in {OUT}')
