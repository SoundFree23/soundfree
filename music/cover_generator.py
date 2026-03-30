"""
Auto-generate cover images from Pixabay when uploading a song.
"""
import os
import re
import hashlib
import logging
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

PIXABAY_API_KEY = os.environ.get('PIXABAY_API_KEY', '55170064-bcd910d5d5d0aaf641a1c0e55')
PIXABAY_URL = 'https://pixabay.com/api/'

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
    'dream': 'dreamy clouds fantasy',
    'cloud': 'clouds sky fluffy',
    'sky': 'blue sky clouds',
    'fire': 'fire flames warm',
    'electric': 'electric neon lights',
    'dance': 'dance music party',
    'city': 'city skyline night',
    'space': 'space galaxy stars',
    'winter': 'winter snow landscape',
    'summer': 'summer beach sun',
    'spring': 'spring flowers bloom',
    'autumn': 'autumn leaves fall',
    'love': 'love heart romantic',
    'deep': 'deep ocean underwater',
    'dark': 'dark moody abstract',
    'light': 'light rays sunshine',
    'gold': 'golden light luxury',
    'smooth': 'smooth silk texture',
    'soul': 'soul music soulful',
    'melody': 'melody music notes',
    'rhythm': 'rhythm drums music',
    'acoustic': 'acoustic guitar wooden',
    'classic': 'classical music elegant',
    'modern': 'modern abstract art',
    'retro': 'retro vintage style',
    'warm': 'warm cozy fireplace',
    'cool': 'cool blue ice',
    'water': 'water drops blue',
    'mountain': 'mountain landscape scenic',
    'tropical': 'tropical beach palm',
    'zen': 'zen meditation peaceful',
    'harmony': 'harmony balance nature',
}

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
    'soul': 'soul music warm vintage',
    'funk': 'funk music colorful groove',
    'minimal': 'minimal abstract clean modern',
    'piano': 'piano keys music elegant',
    'guitar': 'guitar music acoustic strings',
}


def get_search_query(title, genre_name=None):
    title_lower = title.lower()
    for keyword, search_term in KEYWORD_MAP.items():
        if keyword in title_lower:
            return search_term
    if genre_name:
        genre_lower = genre_name.lower()
        for genre_key, search_term in GENRE_SEARCH.items():
            if genre_key in genre_lower:
                return search_term
    clean = re.sub(r'\([^)]*\)', '', title_lower)
    clean = re.sub(r'[0-9]+', '', clean)
    stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'it', 'my', 'your'}
    words = [w for w in clean.split() if w.strip() and w not in stop_words and len(w) > 2]
    if words:
        return ' '.join(words[:3]) + ' music'
    return 'abstract music background'


def search_pixabay(query, per_page=20):
    params = {
        'key': PIXABAY_API_KEY,
        'q': query,
        'image_type': 'photo',
        'orientation': 'horizontal',
        'min_width': 600,
        'min_height': 600,
        'per_page': per_page,
        'safesearch': 'true',
        'order': 'popular',
    }
    try:
        resp = requests.get(PIXABAY_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get('hits', [])
    except requests.RequestException as e:
        logger.warning(f'Pixabay search error: {e}')
        return []


def download_and_crop(url, size=600):
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize((size, size), Image.LANCZOS)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.15)
        return img
    except (requests.RequestException, IOError) as e:
        logger.warning(f'Download/crop error for {url}: {e}')
        return None


def auto_generate_cover(song):
    """
    Automatically generate a cover for a song.
    Called after upload if no cover was provided.
    Returns True if successful.
    """
    title = song.title
    genre_name = song.genre.name if song.genre else None
    query = get_search_query(title, genre_name)

    hits = search_pixabay(query)

    if not hits:
        fallback = (genre_name or 'music') + ' background'
        hits = search_pixabay(fallback)

    if not hits:
        hits = search_pixabay('abstract music art')

    if not hits:
        return False

    # Pick based on title hash
    h = int(hashlib.md5(title.encode()).hexdigest(), 16)
    hit = hits[h % len(hits)]
    img_url = hit.get('webformatURL', '')

    if not img_url:
        return False

    img = download_and_crop(img_url)
    if not img:
        return False

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=92)
    buffer.seek(0)

    filename = f'cover_{song.id}.jpg'
    song.cover_image.save(filename, ContentFile(buffer.read()), save=True)
    return True
