"""
Generate cover images for songs by downloading royalty-free photos from Pixabay.
Searches based on song title keywords and genre.
"""
import re
import hashlib
import requests
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image, ImageFilter, ImageEnhance

PIXABAY_API_KEY = '55170064-bcd910d5d5d0aaf641a1c0e55'
PIXABAY_URL = 'https://pixabay.com/api/'

# Map keywords to better search terms for Pixabay
KEYWORD_MAP = {
    'circuit': 'electronic music abstract',
    'subtle': 'soft light abstract',
    'drift': 'ocean waves dreamy',
    'pulse': 'heartbeat energy light',
    'echo': 'mountains landscape echo',
    'flow': 'water flowing stream',
    'groove': 'music vinyl record',
    'chill': 'relaxing beach sunset',
    'relax': 'relaxation nature calm',
    'calm': 'peaceful lake nature',
    'ambient': 'ambient light abstract',
    'lounge': 'lounge bar evening',
    'cafe': 'coffee cafe cozy',
    'jazz': 'jazz music instruments',
    'blues': 'blues guitar music',
    'rock': 'rock music concert',
    'piano': 'piano keys music',
    'guitar': 'acoustic guitar music',
    'violin': 'violin classical music',
    'night': 'night sky stars city',
    'moon': 'moonlight night sky',
    'star': 'starry night sky',
    'sun': 'sunshine golden light',
    'sunrise': 'sunrise morning sky',
    'sunset': 'sunset evening sky',
    'ocean': 'ocean waves blue',
    'sea': 'sea waves beach',
    'wave': 'ocean wave water',
    'rain': 'rain drops weather',
    'forest': 'forest trees nature',
    'nature': 'nature landscape green',
    'garden': 'garden flowers beautiful',
    'flower': 'flower bloom colorful',
    'rose': 'rose flower red',
    'dream': 'dreamy clouds fantasy',
    'sleep': 'sleep peaceful night',
    'cloud': 'clouds sky fluffy',
    'sky': 'blue sky clouds',
    'fire': 'fire flames warm',
    'electric': 'electric neon lights',
    'neon': 'neon lights city',
    'dance': 'dance music party',
    'party': 'party lights celebration',
    'city': 'city skyline night',
    'urban': 'urban street city',
    'space': 'space galaxy stars',
    'cosmic': 'cosmic galaxy nebula',
    'winter': 'winter snow landscape',
    'snow': 'snow winter cold',
    'summer': 'summer beach sun',
    'spring': 'spring flowers bloom',
    'autumn': 'autumn leaves fall',
    'morning': 'morning light sunrise',
    'evening': 'evening twilight sky',
    'love': 'love heart romantic',
    'heart': 'heart love red',
    'wind': 'wind breeze nature',
    'deep': 'deep ocean underwater',
    'dark': 'dark moody abstract',
    'light': 'light rays sunshine',
    'bright': 'bright colorful light',
    'gold': 'golden light luxury',
    'crystal': 'crystal clear water',
    'smooth': 'smooth silk texture',
    'soft': 'soft light pastel',
    'gentle': 'gentle nature peaceful',
    'soul': 'soul music soulful',
    'funk': 'funky colorful music',
    'minimal': 'minimal clean white',
    'warm': 'warm cozy fireplace',
    'cool': 'cool blue ice',
    'water': 'water drops blue',
    'tree': 'tree nature green',
    'mountain': 'mountain landscape scenic',
    'river': 'river flowing water',
    'lake': 'lake calm reflection',
    'desert': 'desert sand dunes',
    'tropical': 'tropical beach palm',
    'island': 'island paradise tropical',
    'mystic': 'mystic fog mysterious',
    'magic': 'magical fantasy light',
    'zen': 'zen meditation peaceful',
    'harmony': 'harmony balance nature',
    'melody': 'melody music notes',
    'rhythm': 'rhythm drums music',
    'beat': 'beat drums percussion',
    'bass': 'bass guitar music',
    'vocal': 'singing microphone music',
    'acoustic': 'acoustic guitar wooden',
    'classic': 'classical music elegant',
    'modern': 'modern abstract art',
    'retro': 'retro vintage style',
    'vintage': 'vintage old classic',
}

# Genre-based search terms
GENRE_SEARCH = {
    'jazz': 'jazz music saxophone piano',
    'blues': 'blues guitar music moody',
    'rock': 'rock music concert electric',
    'pop': 'pop music colorful bright',
    'classical': 'classical music orchestra elegant',
    'electronic': 'electronic music neon lights',
    'ambient': 'ambient nature peaceful calm',
    'lounge': 'lounge bar evening relaxing',
    'chill': 'chill relaxing beach sunset',
    'folk': 'folk acoustic guitar nature',
    'r&b': 'soul music urban night',
    'hip-hop': 'urban street city night',
    'country': 'country music landscape rural',
    'reggae': 'reggae tropical beach colorful',
    'latin': 'latin music dance colorful',
    'world': 'world music culture instruments',
    'funk': 'funk music colorful groove',
    'soul': 'soul music warm vintage',
    'metal': 'metal dark concert energy',
    'punk': 'punk concert energy urban',
    'indie': 'indie music artistic creative',
    'new-age': 'meditation peaceful spiritual nature',
    'soundtrack': 'cinematic landscape dramatic',
    'piano': 'piano keys music elegant',
    'guitar': 'guitar music acoustic strings',
    'minimal': 'minimal abstract clean modern',
}


def get_search_query(title, genre_name=None):
    """Build a search query from song title and genre."""
    title_lower = title.lower()

    # Check keyword map first
    for keyword, search_term in KEYWORD_MAP.items():
        if keyword in title_lower:
            return search_term

    # Check genre
    if genre_name:
        genre_lower = genre_name.lower()
        for genre_key, search_term in GENRE_SEARCH.items():
            if genre_key in genre_lower:
                return search_term

    # Fallback: clean the title and use it as search
    # Remove common non-descriptive words and parentheses content
    clean = re.sub(r'\([^)]*\)', '', title_lower)  # remove (minimal1) etc
    clean = re.sub(r'[0-9]+', '', clean)  # remove numbers
    stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'it', 'my', 'your'}
    words = [w for w in clean.split() if w.strip() and w not in stop_words and len(w) > 2]

    if words:
        return ' '.join(words[:3]) + ' music'

    # Last resort
    return 'abstract music background'


def search_pixabay(query, per_page=30, page=1):
    """Search Pixabay for images."""
    params = {
        'key': PIXABAY_API_KEY,
        'q': query,
        'image_type': 'photo',
        'orientation': 'horizontal',
        'min_width': 600,
        'min_height': 600,
        'per_page': per_page,
        'page': page,
        'safesearch': 'true',
        'order': 'popular',
    }
    try:
        resp = requests.get(PIXABAY_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get('hits', [])
    except Exception as e:
        print(f'  Pixabay search error: {e}')
        return []


def download_and_crop(url, size=600):
    """Download image and crop to square."""
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Crop to square (center crop)
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))

        # Resize to target size
        img = img.resize((size, size), Image.LANCZOS)

        # Slight enhancements
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.15)

        return img
    except Exception as e:
        print(f'  Download error: {e}')
        return None


def pick_unique_image(hits, title, used_image_ids):
    """Pick an image that hasn't been used yet."""
    if not hits:
        return None

    # Filter out already used images
    available = [h for h in hits if h.get('id') not in used_image_ids]

    if not available:
        # All images from this search were used, return None to trigger new search
        return None

    # Pick deterministically from available
    h = int(hashlib.md5(title.encode()).hexdigest(), 16)
    idx = h % len(available)
    return available[idx]


class Command(BaseCommand):
    help = 'Generate cover images by downloading from Pixabay'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Regenerate all covers')
        parser.add_argument('--replace-generated', action='store_true', help='Replace only previously generated covers')

    def handle(self, *args, **options):
        from music.models import Song

        # Always process ALL songs when --force
        if options['force']:
            songs = Song.objects.all()
        elif options['replace_generated']:
            songs = Song.objects.filter(cover_image__startswith='covers/cover_')
        else:
            songs = Song.objects.filter(cover_image='') | Song.objects.filter(cover_image__isnull=True)

        count = songs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('All songs already have covers!'))
            return

        self.stdout.write(f'Generating covers for {count} songs...')

        success = 0
        failed = 0
        used_image_ids = set()  # Track all used Pixabay image IDs to avoid duplicates

        for song in songs:
            title = song.title
            genre_name = song.genre.name if song.genre else None
            query = get_search_query(title, genre_name)
            self.stdout.write(f'  {title} -> searching: "{query}"')

            # Try multiple pages to find unique images
            hit = None
            for page in range(1, 4):  # Try up to 3 pages
                hits = search_pixabay(query, per_page=30, page=page)

                if not hits:
                    break

                hit = pick_unique_image(hits, title, used_image_ids)
                if hit:
                    break

            # Fallback search if no unique image found
            if not hit:
                fallback_queries = [
                    (genre_name or 'music') + ' background',
                    'abstract music art',
                    'music instrument artistic',
                    'concert live music',
                    'studio recording music',
                ]
                for fq in fallback_queries:
                    self.stdout.write(f'    Trying fallback: "{fq}"')
                    hits = search_pixabay(fq, per_page=30)
                    if hits:
                        hit = pick_unique_image(hits, title + fq, used_image_ids)
                        if hit:
                            break

            if not hit:
                self.stdout.write(self.style.WARNING(f'    No unique image found for: {title}'))
                failed += 1
                continue

            img_url = hit.get('webformatURL', '')
            img_id = hit.get('id')

            if not img_url:
                failed += 1
                continue

            self.stdout.write(f'    Downloading image #{img_id}...')
            img = download_and_crop(img_url)

            if not img:
                failed += 1
                continue

            # Mark this image as used
            used_image_ids.add(img_id)

            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=92)
            buffer.seek(0)

            filename = f'cover_{song.id}.jpg'
            song.cover_image.save(filename, ContentFile(buffer.read()), save=True)
            success += 1
            self.stdout.write(self.style.SUCCESS(f'    Done! (unique images used: {len(used_image_ids)})'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Finished! {success} covers generated, {failed} failed.'))
        self.stdout.write(f'Total unique images used: {len(used_image_ids)}')
