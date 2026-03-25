"""
Generate artistic cover images for songs that don't have one.
Creates abstract art inspired by the song title keywords - no text.
"""
import math
import random
import hashlib
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFilter


# Theme keywords -> color palettes + pattern style
THEMES = {
    'ocean': {'colors': [(10, 40, 80), (20, 100, 170), (60, 180, 220), (200, 230, 250)], 'style': 'waves'},
    'sea': {'colors': [(10, 40, 80), (20, 100, 170), (60, 180, 220), (200, 230, 250)], 'style': 'waves'},
    'water': {'colors': [(10, 50, 90), (30, 120, 180), (80, 190, 230), (180, 220, 245)], 'style': 'waves'},
    'wave': {'colors': [(15, 45, 85), (25, 110, 175), (70, 185, 225), (190, 225, 248)], 'style': 'waves'},
    'rain': {'colors': [(30, 40, 60), (50, 70, 100), (100, 130, 170), (160, 180, 210)], 'style': 'drops'},
    'night': {'colors': [(5, 5, 20), (15, 10, 40), (30, 20, 70), (60, 40, 120)], 'style': 'stars'},
    'star': {'colors': [(5, 5, 25), (10, 10, 45), (25, 15, 65), (200, 180, 100)], 'style': 'stars'},
    'moon': {'colors': [(10, 10, 30), (20, 20, 50), (40, 35, 80), (220, 210, 170)], 'style': 'circles'},
    'sun': {'colors': [(255, 180, 50), (255, 130, 30), (230, 80, 20), (180, 40, 10)], 'style': 'radial'},
    'sunrise': {'colors': [(255, 180, 80), (255, 120, 60), (200, 60, 80), (60, 20, 80)], 'style': 'horizon'},
    'sunset': {'colors': [(255, 150, 50), (230, 80, 50), (150, 30, 70), (40, 10, 60)], 'style': 'horizon'},
    'fire': {'colors': [(255, 200, 50), (255, 130, 20), (220, 50, 10), (120, 20, 5)], 'style': 'flames'},
    'forest': {'colors': [(10, 30, 10), (20, 60, 15), (30, 100, 25), (50, 140, 40)], 'style': 'organic'},
    'tree': {'colors': [(15, 35, 12), (25, 65, 18), (35, 105, 28), (55, 145, 42)], 'style': 'organic'},
    'nature': {'colors': [(20, 50, 15), (40, 90, 30), (60, 130, 45), (100, 170, 70)], 'style': 'organic'},
    'garden': {'colors': [(30, 70, 20), (60, 120, 40), (100, 160, 60), (180, 200, 100)], 'style': 'organic'},
    'flower': {'colors': [(200, 60, 100), (230, 100, 140), (240, 150, 180), (250, 200, 210)], 'style': 'petals'},
    'rose': {'colors': [(180, 20, 50), (210, 50, 80), (230, 100, 120), (245, 170, 180)], 'style': 'petals'},
    'love': {'colors': [(180, 20, 60), (220, 40, 80), (240, 80, 120), (250, 150, 170)], 'style': 'circles'},
    'heart': {'colors': [(190, 25, 55), (225, 45, 85), (245, 90, 125), (250, 160, 175)], 'style': 'circles'},
    'dream': {'colors': [(80, 40, 140), (120, 60, 180), (160, 100, 210), (200, 160, 240)], 'style': 'bubbles'},
    'sleep': {'colors': [(20, 15, 50), (40, 30, 80), (70, 50, 120), (120, 90, 170)], 'style': 'bubbles'},
    'cloud': {'colors': [(100, 140, 180), (140, 170, 200), (180, 200, 220), (220, 230, 240)], 'style': 'bubbles'},
    'sky': {'colors': [(30, 100, 200), (60, 140, 220), (100, 175, 235), (160, 210, 250)], 'style': 'radial'},
    'jazz': {'colors': [(40, 20, 10), (80, 40, 15), (140, 80, 30), (200, 150, 60)], 'style': 'geometric'},
    'blues': {'colors': [(10, 20, 60), (20, 40, 100), (40, 70, 150), (80, 120, 200)], 'style': 'geometric'},
    'rock': {'colors': [(30, 30, 30), (60, 50, 50), (100, 70, 60), (150, 100, 80)], 'style': 'angular'},
    'metal': {'colors': [(20, 20, 25), (50, 50, 60), (90, 90, 100), (140, 140, 155)], 'style': 'angular'},
    'electric': {'colors': [(0, 200, 255), (0, 100, 255), (80, 0, 200), (150, 0, 255)], 'style': 'lightning'},
    'neon': {'colors': [(255, 0, 150), (0, 255, 200), (150, 0, 255), (255, 255, 0)], 'style': 'geometric'},
    'piano': {'colors': [(20, 20, 25), (60, 55, 65), (120, 110, 125), (200, 190, 205)], 'style': 'geometric'},
    'guitar': {'colors': [(100, 50, 20), (150, 80, 30), (190, 120, 50), (220, 170, 80)], 'style': 'geometric'},
    'violin': {'colors': [(80, 30, 10), (130, 60, 20), (170, 100, 40), (210, 150, 70)], 'style': 'geometric'},
    'chill': {'colors': [(40, 60, 90), (60, 90, 130), (90, 130, 170), (140, 180, 210)], 'style': 'bubbles'},
    'relax': {'colors': [(50, 70, 100), (70, 100, 140), (100, 140, 180), (150, 190, 220)], 'style': 'bubbles'},
    'calm': {'colors': [(45, 65, 95), (65, 95, 135), (95, 135, 175), (145, 185, 215)], 'style': 'bubbles'},
    'ambient': {'colors': [(30, 40, 60), (50, 65, 90), (80, 100, 140), (130, 155, 190)], 'style': 'bubbles'},
    'lounge': {'colors': [(50, 30, 60), (80, 50, 90), (120, 80, 130), (170, 130, 180)], 'style': 'circles'},
    'cafe': {'colors': [(60, 35, 20), (100, 60, 30), (150, 100, 55), (200, 160, 100)], 'style': 'circles'},
    'coffee': {'colors': [(55, 30, 15), (95, 55, 25), (145, 95, 50), (195, 155, 95)], 'style': 'circles'},
    'morning': {'colors': [(255, 210, 140), (255, 180, 100), (240, 140, 80), (200, 100, 60)], 'style': 'radial'},
    'evening': {'colors': [(80, 40, 100), (120, 60, 130), (160, 80, 140), (200, 120, 150)], 'style': 'horizon'},
    'winter': {'colors': [(180, 210, 240), (140, 180, 220), (100, 150, 200), (60, 110, 170)], 'style': 'drops'},
    'snow': {'colors': [(200, 220, 240), (170, 195, 225), (140, 170, 210), (110, 140, 185)], 'style': 'drops'},
    'summer': {'colors': [(255, 200, 50), (255, 150, 40), (240, 100, 30), (200, 60, 20)], 'style': 'radial'},
    'spring': {'colors': [(100, 200, 100), (140, 210, 120), (180, 220, 150), (220, 240, 190)], 'style': 'petals'},
    'autumn': {'colors': [(200, 100, 30), (180, 70, 20), (150, 50, 15), (100, 30, 10)], 'style': 'organic'},
    'dance': {'colors': [(255, 50, 100), (200, 30, 150), (130, 20, 200), (60, 10, 230)], 'style': 'geometric'},
    'party': {'colors': [(255, 40, 90), (190, 25, 145), (125, 15, 195), (55, 5, 225)], 'style': 'geometric'},
    'city': {'colors': [(30, 30, 40), (50, 50, 65), (80, 80, 100), (120, 120, 145)], 'style': 'angular'},
    'urban': {'colors': [(35, 35, 45), (55, 55, 70), (85, 85, 105), (125, 125, 150)], 'style': 'angular'},
    'street': {'colors': [(40, 40, 50), (60, 60, 75), (90, 90, 110), (130, 130, 155)], 'style': 'angular'},
    'space': {'colors': [(5, 0, 15), (15, 5, 40), (30, 10, 70), (50, 20, 110)], 'style': 'stars'},
    'cosmic': {'colors': [(8, 2, 18), (18, 8, 45), (33, 13, 75), (55, 25, 115)], 'style': 'stars'},
    'wind': {'colors': [(140, 170, 200), (170, 195, 220), (195, 215, 235), (220, 235, 248)], 'style': 'waves'},
    'breath': {'colors': [(130, 165, 195), (165, 190, 215), (190, 210, 230), (215, 230, 245)], 'style': 'waves'},
    'silent': {'colors': [(15, 15, 20), (30, 30, 40), (50, 50, 65), (80, 80, 100)], 'style': 'minimal'},
    'quiet': {'colors': [(20, 20, 25), (35, 35, 45), (55, 55, 70), (85, 85, 105)], 'style': 'minimal'},
    'gentle': {'colors': [(180, 200, 210), (160, 185, 200), (140, 165, 185), (120, 145, 165)], 'style': 'minimal'},
    'soft': {'colors': [(200, 190, 210), (185, 175, 200), (165, 155, 185), (145, 135, 165)], 'style': 'minimal'},
    'deep': {'colors': [(10, 10, 30), (15, 15, 50), (25, 20, 75), (40, 30, 110)], 'style': 'radial'},
    'dark': {'colors': [(10, 10, 15), (20, 18, 25), (35, 30, 40), (55, 48, 60)], 'style': 'minimal'},
    'light': {'colors': [(240, 235, 220), (230, 220, 200), (215, 200, 180), (195, 180, 160)], 'style': 'radial'},
    'bright': {'colors': [(255, 240, 200), (255, 220, 160), (255, 195, 120), (250, 170, 80)], 'style': 'radial'},
    'gold': {'colors': [(255, 200, 50), (230, 170, 30), (200, 140, 20), (160, 110, 10)], 'style': 'radial'},
    'crystal': {'colors': [(180, 220, 240), (150, 200, 235), (120, 180, 230), (80, 150, 220)], 'style': 'geometric'},
    'minimal': {'colors': [(240, 240, 240), (200, 200, 205), (160, 160, 170), (120, 120, 135)], 'style': 'minimal'},
    'smooth': {'colors': [(60, 50, 80), (90, 75, 115), (125, 105, 155), (165, 145, 195)], 'style': 'bubbles'},
    'groove': {'colors': [(180, 60, 30), (200, 90, 40), (220, 130, 60), (240, 180, 90)], 'style': 'geometric'},
    'funk': {'colors': [(200, 50, 50), (220, 100, 30), (240, 170, 20), (100, 200, 50)], 'style': 'geometric'},
    'soul': {'colors': [(100, 40, 20), (140, 60, 30), (180, 90, 45), (220, 140, 70)], 'style': 'circles'},
    'echo': {'colors': [(40, 50, 70), (60, 75, 100), (90, 110, 140), (130, 155, 185)], 'style': 'circles'},
    'pulse': {'colors': [(200, 30, 60), (170, 20, 80), (130, 15, 100), (80, 10, 120)], 'style': 'circles'},
    'flow': {'colors': [(30, 80, 140), (50, 120, 180), (80, 160, 210), (130, 200, 235)], 'style': 'waves'},
    'drift': {'colors': [(60, 80, 120), (80, 110, 155), (110, 145, 190), (150, 185, 220)], 'style': 'waves'},
    'circuit': {'colors': [(0, 180, 200), (0, 140, 180), (0, 100, 150), (0, 60, 120)], 'style': 'geometric'},
    'subtle': {'colors': [(180, 175, 190), (165, 158, 175), (148, 140, 158), (130, 122, 140)], 'style': 'minimal'},
}

# Default palettes for songs that don't match any keyword
DEFAULT_PALETTES = [
    {'colors': [(40, 80, 140), (60, 120, 180), (100, 160, 210), (160, 200, 235)], 'style': 'waves'},
    {'colors': [(140, 40, 80), (180, 60, 100), (210, 100, 140), (235, 160, 190)], 'style': 'circles'},
    {'colors': [(40, 100, 60), (60, 140, 80), (100, 180, 110), (160, 210, 160)], 'style': 'organic'},
    {'colors': [(80, 40, 140), (120, 60, 180), (160, 100, 210), (200, 160, 235)], 'style': 'bubbles'},
    {'colors': [(140, 100, 40), (180, 140, 60), (210, 180, 100), (235, 210, 160)], 'style': 'geometric'},
    {'colors': [(40, 60, 80), (65, 90, 115), (95, 125, 155), (135, 165, 200)], 'style': 'minimal'},
    {'colors': [(100, 50, 80), (140, 75, 110), (180, 110, 145), (215, 155, 185)], 'style': 'radial'},
    {'colors': [(50, 90, 90), (75, 130, 125), (110, 170, 160), (155, 205, 195)], 'style': 'horizon'},
    {'colors': [(120, 60, 30), (160, 90, 45), (195, 130, 70), (225, 175, 110)], 'style': 'angular'},
    {'colors': [(60, 40, 100), (90, 60, 140), (130, 95, 180), (175, 140, 215)], 'style': 'stars'},
]


def seed_random(title):
    """Create a seeded random generator for deterministic results."""
    h = int(hashlib.md5(title.encode()).hexdigest(), 16)
    return random.Random(h)


def get_theme(title):
    """Find the best matching theme for a song title."""
    title_lower = title.lower()
    for keyword, theme in THEMES.items():
        if keyword in title_lower:
            return theme
    # Default: pick based on title hash
    rng = seed_random(title)
    return rng.choice(DEFAULT_PALETTES)


def lerp_color(c1, c2, t):
    """Linear interpolation between two colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def draw_gradient(img, colors, angle=0):
    """Draw a multi-stop gradient."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        for x in range(w):
            # Rotated gradient
            t = (math.cos(math.radians(angle)) * x + math.sin(math.radians(angle)) * y) / (w + h) * 2
            t = max(0, min(1, t + 0.3))
            # Multi-stop
            n = len(colors) - 1
            idx = int(t * n)
            idx = min(idx, n - 1)
            local_t = (t * n) - idx
            color = lerp_color(colors[idx], colors[idx + 1], local_t)
            draw.point((x, y), fill=color)


def draw_waves(img, colors, rng):
    """Draw flowing wave patterns."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw_gradient(img, colors, angle=30)
    # Add wave lines
    for i in range(5):
        wave_y = h * (0.2 + i * 0.15)
        amplitude = 20 + rng.random() * 30
        freq = 0.008 + rng.random() * 0.005
        phase = rng.random() * math.pi * 2
        c = lerp_color(colors[-1], (255, 255, 255), 0.1 + i * 0.05)
        points = []
        for x in range(0, w + 1, 2):
            y = wave_y + math.sin(x * freq + phase) * amplitude
            points.append((x, y))
        # Draw as a filled area below
        points_bottom = [(w, h), (0, h)]
        polygon = points + points_bottom
        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.polygon(polygon, fill=(*c, 25 + i * 8))
        img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_circles(img, colors, rng):
    """Draw overlapping circles."""
    draw_gradient(img, colors, angle=45)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(8, 15)):
        cx = rng.randint(-50, w + 50)
        cy = rng.randint(-50, h + 50)
        r = rng.randint(40, 180)
        c = rng.choice(colors)
        alpha = rng.randint(30, 70)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, alpha))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_stars(img, colors, rng):
    """Draw starfield pattern."""
    draw_gradient(img, colors[:2], angle=60)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for _ in range(rng.randint(80, 200)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        brightness = rng.randint(150, 255)
        size = rng.choice([1, 1, 1, 2, 2, 3])
        c = (brightness, brightness, rng.randint(brightness - 30, brightness))
        if size == 1:
            draw.point((x, y), fill=c)
        else:
            draw.ellipse((x - size, y - size, x + size, y + size), fill=c)
    # Add a couple of bigger glowing stars
    for _ in range(rng.randint(2, 5)):
        cx, cy = rng.randint(50, w - 50), rng.randint(50, h - 50)
        for r in range(12, 0, -1):
            alpha = int(80 * (1 - r / 12))
            c = lerp_color(colors[-1], (255, 255, 255), 0.5)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c,))


def draw_bubbles(img, colors, rng):
    """Draw soft bubble/bokeh effect."""
    draw_gradient(img, colors, angle=135)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(15, 30)):
        cx = rng.randint(-30, w + 30)
        cy = rng.randint(-30, h + 30)
        r = rng.randint(15, 80)
        c = rng.choice(colors)
        alpha = rng.randint(15, 45)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, alpha))
        # Highlight
        od.ellipse((cx - r // 3, cy - r // 3, cx, cy), fill=(255, 255, 255, 10))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_geometric(img, colors, rng):
    """Draw geometric shapes."""
    draw_gradient(img, colors, angle=45)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(6, 14)):
        shape = rng.choice(['rect', 'tri', 'line'])
        c = rng.choice(colors)
        alpha = rng.randint(25, 65)
        if shape == 'rect':
            x1 = rng.randint(-20, w)
            y1 = rng.randint(-20, h)
            x2 = x1 + rng.randint(40, 200)
            y2 = y1 + rng.randint(40, 200)
            angle = rng.randint(0, 45)
            od.rectangle((x1, y1, x2, y2), fill=(*c, alpha))
        elif shape == 'tri':
            pts = [(rng.randint(0, w), rng.randint(0, h)) for _ in range(3)]
            od.polygon(pts, fill=(*c, alpha))
        else:
            x1, y1 = rng.randint(0, w), rng.randint(0, h)
            x2, y2 = rng.randint(0, w), rng.randint(0, h)
            od.line((x1, y1, x2, y2), fill=(*c, alpha), width=rng.randint(2, 8))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_organic(img, colors, rng):
    """Draw organic/natural shapes."""
    draw_gradient(img, colors, angle=60)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(8, 16)):
        cx = rng.randint(0, w)
        cy = rng.randint(0, h)
        c = rng.choice(colors)
        alpha = rng.randint(20, 55)
        pts = []
        n_pts = rng.randint(5, 8)
        base_r = rng.randint(30, 120)
        for i in range(n_pts):
            angle = (2 * math.pi * i) / n_pts
            r = base_r + rng.randint(-20, 20)
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            pts.append((px, py))
        if len(pts) >= 3:
            od.polygon(pts, fill=(*c, alpha))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_radial(img, colors, rng):
    """Draw radial gradient with glow."""
    w, h = img.size
    draw_gradient(img, colors, angle=0)
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx = w * (0.3 + rng.random() * 0.4)
    cy = h * (0.3 + rng.random() * 0.4)
    max_r = int(w * 0.6)
    for r in range(max_r, 0, -2):
        t = 1 - (r / max_r)
        c = lerp_color(colors[0], colors[-1], t)
        alpha = int(80 * t)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, alpha))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_horizon(img, colors, rng):
    """Draw horizon/sunset style."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        n = len(colors) - 1
        idx = min(int(t * n), n - 1)
        local_t = (t * n) - idx
        color = lerp_color(colors[idx], colors[idx + 1], local_t)
        draw.line([(0, y), (w, y)], fill=color)
    # Add sun circle
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    sun_y = int(h * 0.45)
    sun_x = int(w * 0.5)
    for r in range(80, 0, -1):
        alpha = int(200 * (1 - r / 80))
        c = lerp_color(colors[0], (255, 255, 255), 0.3)
        od.ellipse((sun_x - r, sun_y - r, sun_x + r, sun_y + r), fill=(*c, alpha))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_angular(img, colors, rng):
    """Draw angular/sharp geometric."""
    draw_gradient(img, colors, angle=30)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(5, 10)):
        pts = [(rng.randint(0, w), rng.randint(0, h)) for _ in range(rng.randint(3, 5))]
        c = rng.choice(colors)
        alpha = rng.randint(25, 60)
        od.polygon(pts, fill=(*c, alpha))
    # Add sharp lines
    for _ in range(rng.randint(3, 8)):
        x1, y1 = rng.randint(0, w), rng.randint(0, h)
        x2, y2 = rng.randint(0, w), rng.randint(0, h)
        c = lerp_color(rng.choice(colors), (255, 255, 255), 0.2)
        od.line((x1, y1, x2, y2), fill=(*c, 40), width=rng.randint(1, 4))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_drops(img, colors, rng):
    """Draw raindrop/snow pattern."""
    draw_gradient(img, colors, angle=90)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for _ in range(rng.randint(40, 100)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        length = rng.randint(5, 25)
        c = lerp_color(colors[-1], (255, 255, 255), 0.3 + rng.random() * 0.3)
        alpha_val = rng.randint(80, 180)
        draw.line((x, y, x + 1, y + length), fill=(*c,), width=1)


def draw_petals(img, colors, rng):
    """Draw flower petal shapes."""
    draw_gradient(img, colors, angle=45)
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(8, 18)):
        cx = rng.randint(0, w)
        cy = rng.randint(0, h)
        c = rng.choice(colors)
        alpha = rng.randint(25, 60)
        rx = rng.randint(15, 50)
        ry = rng.randint(30, 80)
        od.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(*c, alpha))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_flames(img, colors, rng):
    """Draw fire/flame style."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        n = len(colors) - 1
        idx = min(int(t * n), n - 1)
        local_t = (t * n) - idx
        color = lerp_color(colors[idx], colors[idx + 1], local_t)
        draw.line([(0, y), (w, y)], fill=color)
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(10, 20)):
        cx = rng.randint(0, w)
        base_y = h
        c = rng.choice(colors[:2])
        pts = []
        height = rng.randint(100, 350)
        width = rng.randint(20, 60)
        pts = [
            (cx - width, base_y),
            (cx - width // 3, base_y - height * 0.6),
            (cx, base_y - height),
            (cx + width // 3, base_y - height * 0.6),
            (cx + width, base_y),
        ]
        od.polygon(pts, fill=(*c, rng.randint(20, 50)))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


def draw_lightning(img, colors, rng):
    """Draw electric/lightning pattern."""
    draw_gradient(img, [colors[2], colors[3], colors[0]], angle=60)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for _ in range(rng.randint(3, 7)):
        x = rng.randint(50, w - 50)
        y = 0
        c = rng.choice(colors[:2])
        while y < h:
            nx = x + rng.randint(-30, 30)
            ny = y + rng.randint(10, 40)
            draw.line((x, y, nx, ny), fill=c, width=rng.randint(1, 3))
            x, y = nx, ny


def draw_minimal(img, colors, rng):
    """Draw minimal/clean style."""
    draw_gradient(img, colors, angle=rng.randint(0, 180))
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # Just a few subtle shapes
    for _ in range(rng.randint(2, 4)):
        cx = rng.randint(w // 4, 3 * w // 4)
        cy = rng.randint(h // 4, 3 * h // 4)
        r = rng.randint(50, 150)
        c = rng.choice(colors)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*c, 20))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))


STYLE_FUNCS = {
    'waves': draw_waves,
    'circles': draw_circles,
    'stars': draw_stars,
    'bubbles': draw_bubbles,
    'geometric': draw_geometric,
    'organic': draw_organic,
    'radial': draw_radial,
    'horizon': draw_horizon,
    'angular': draw_angular,
    'drops': draw_drops,
    'petals': draw_petals,
    'flames': draw_flames,
    'lightning': draw_lightning,
    'minimal': draw_minimal,
}


def create_cover(title, size=600):
    """Create an artistic cover image inspired by the song title."""
    rng = seed_random(title)
    theme = get_theme(title)
    colors = theme['colors']
    style = theme['style']

    img = Image.new('RGB', (size, size), colors[0])

    # Draw the pattern
    draw_func = STYLE_FUNCS.get(style, draw_minimal)
    draw_func(img, colors, rng)

    # Apply slight blur for smoothness
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    return img


class Command(BaseCommand):
    help = 'Generate artistic cover images for songs without covers'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Regenerate all covers')
        parser.add_argument('--replace-generated', action='store_true', help='Replace only previously generated covers (cover_*.jpg)')

    def handle(self, *args, **options):
        from music.models import Song

        if options['replace_generated']:
            # Only replace covers that were generated by this script (cover_ID.jpg)
            songs = Song.objects.filter(cover_image__startswith='covers/cover_')
        elif options['force']:
            songs = Song.objects.all()
        else:
            songs = Song.objects.filter(cover_image='') | Song.objects.filter(cover_image__isnull=True)

        count = songs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('All songs already have covers!'))
            return

        self.stdout.write(f'Generating covers for {count} songs...')

        for song in songs:
            title = song.title
            theme = get_theme(title)
            self.stdout.write(f'  {title} -> style: {theme["style"]}')

            img = create_cover(title)

            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            buffer.seek(0)

            filename = f'cover_{song.id}.jpg'
            song.cover_image.save(filename, ContentFile(buffer.read()), save=True)

        self.stdout.write(self.style.SUCCESS(f'Done! Generated {count} artistic covers.'))
