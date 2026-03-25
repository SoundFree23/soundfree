"""
Generate cover images for songs that don't have one.
Creates gradient backgrounds with the song title text.
"""
import os
import math
import hashlib
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


# Color palettes for gradients
PALETTES = [
    [(29, 185, 84), (21, 120, 60)],       # Spotify green
    [(225, 51, 0), (150, 30, 0)],          # Red
    [(132, 0, 231), (80, 0, 150)],         # Purple
    [(30, 50, 100), (10, 20, 60)],         # Navy
    [(232, 17, 91), (160, 10, 60)],        # Pink
    [(20, 138, 8), (10, 80, 5)],           # Forest green
    [(80, 155, 245), (40, 80, 160)],       # Blue
    [(245, 155, 35), (180, 100, 20)],      # Orange
    [(186, 93, 7), (120, 60, 5)],          # Brown
    [(39, 133, 106), (20, 80, 65)],        # Teal
    [(175, 40, 150), (100, 20, 90)],       # Magenta
    [(13, 115, 236), (8, 70, 150)],        # Royal blue
    [(96, 129, 8), (60, 80, 5)],           # Olive
    [(141, 103, 171), (90, 60, 110)],      # Lavender
    [(71, 125, 149), (40, 75, 95)],        # Steel blue
]


def get_palette_for_title(title):
    """Deterministic color based on title."""
    h = int(hashlib.md5(title.encode()).hexdigest(), 16)
    return PALETTES[h % len(PALETTES)]


def create_cover(title, size=600):
    """Create a gradient cover image with title text."""
    img = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(img)

    # Get colors
    c1, c2 = get_palette_for_title(title)

    # Draw diagonal gradient
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            img.putpixel((x, y), (r, g, b))

    # Add subtle texture - darker circle in bottom right
    for y in range(size):
        for x in range(size):
            dx = x - size * 0.75
            dy = y - size * 0.75
            dist = math.sqrt(dx*dx + dy*dy) / (size * 0.5)
            if dist < 1:
                pixel = img.getpixel((x, y))
                factor = 0.85 + 0.15 * dist
                img.putpixel((x, y), (
                    int(pixel[0] * factor),
                    int(pixel[1] * factor),
                    int(pixel[2] * factor),
                ))

    # Add title text
    # Try to find a good font
    font = None
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 42)
                break
            except Exception:
                pass
    if not font:
        try:
            font = ImageFont.truetype("arial.ttf", 42)
        except Exception:
            font = ImageFont.load_default()

    # Word wrap the title
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > size - 80:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    # Draw text centered
    line_height = 52
    total_height = len(lines) * line_height
    y_start = (size - total_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (size - tw) // 2
        y = y_start + i * line_height
        # Shadow
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 128), font=font)
        # Main text
        draw.text((x, y), line, fill=(255, 255, 255), font=font)

    # Add a small music note icon in bottom-left
    try:
        small_font = ImageFont.truetype(font_paths[0] if os.path.exists(font_paths[0]) else "arial.ttf", 28)
    except Exception:
        small_font = font

    return img


class Command(BaseCommand):
    help = 'Generate cover images for songs without covers'

    def handle(self, *args, **options):
        from music.models import Song

        songs = Song.objects.filter(cover_image='') | Song.objects.filter(cover_image__isnull=True)
        count = songs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('All songs already have covers!'))
            return

        self.stdout.write(f'Generating covers for {count} songs...')

        for song in songs:
            title = song.title
            self.stdout.write(f'  Creating cover for: {title}')

            img = create_cover(title)

            # Save to BytesIO
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            buffer.seek(0)

            # Save to model
            filename = f'cover_{song.id}.jpg'
            song.cover_image.save(filename, ContentFile(buffer.read()), save=True)

        self.stdout.write(self.style.SUCCESS(f'Done! Generated {count} covers.'))
