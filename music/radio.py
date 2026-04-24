"""
Radio SoundFree — selectează automat melodii în funcție de oră și zi.
Rotație 100% automată. Fusul orar folosit: Europe/Bucharest (din settings.TIME_ZONE).
"""
from django.db.models import Q
from django.utils import timezone
from .models import Song


# Fiecare slot are:
#   id        - identificator stabil
#   emoji     - iconiță pentru UI
#   name_ro   - titlu afișat în română
#   name_en   - titlu afișat în engleză
#   genres    - listă de slug-uri de genuri (OR)
#   moods     - listă de slug-uri de mood-uri (OR)
# Melodia trebuie să se potrivească cu cel puțin un gen SAU un mood.
SLOTS = {
    'morning': {
        'emoji': '☀️',
        'name_ro': 'Dimineața Activă',
        'name_en': 'Morning Boost',
        'genres': ['upbeat-retail', 'pop-instrumental', 'pop', 'acoustic'],
        'moods': ['vesel', 'energic'],
    },
    'focus': {
        'emoji': '☕',
        'name_ro': 'Focus & Work',
        'name_en': 'Focus & Work',
        'genres': ['ambient', 'jazz-lounge', 'classical-modern', 'cafe-music', 'electronic-chill', 'pop-instrumental'],
        'moods': ['profesional', 'relaxant'],
    },
    'afternoon': {
        'emoji': '🌤️',
        'name_ro': 'După-amiază',
        'name_en': 'Afternoon Flow',
        'genres': ['pop', 'pop-instrumental', 'electronic-chill', 'upbeat-retail', 'acoustic'],
        'moods': ['energic', 'vesel'],
    },
    'evening': {
        'emoji': '🌆',
        'name_ro': 'Seară Relaxantă',
        'name_en': 'Evening Chill',
        'genres': ['jazz-lounge', 'lounge', 'acoustic', 'jazz', 'rb', 'cafe-music'],
        'moods': ['relaxant', 'romantic'],
    },
    'night': {
        'emoji': '🌙',
        'name_ro': 'Noapte Lounge',
        'name_en': 'Night Lounge',
        'genres': ['ambient', 'lounge', 'jazz-lounge', 'electronic-chill', 'classical-modern'],
        'moods': ['misterios', 'relaxant'],
    },
    'late_night': {
        'emoji': '🌌',
        'name_ro': 'Somn Adânc',
        'name_en': 'Deep Sleep',
        'genres': ['ambient', 'classical-modern'],
        'moods': ['relaxant'],
    },
    'weekend_party': {
        'emoji': '🎉',
        'name_ro': 'Weekend Party',
        'name_en': 'Weekend Party',
        'genres': ['pop', 'disco', 'house', 'rock', 'upbeat-retail', 'electronic-chill'],
        'moods': ['energic', 'vesel'],
    },
    'weekend_morning': {
        'emoji': '🌅',
        'name_ro': 'Dimineață de Weekend',
        'name_en': 'Weekend Morning',
        'genres': ['acoustic', 'cafe-music', 'jazz-lounge', 'pop-instrumental'],
        'moods': ['relaxant', 'romantic', 'vesel'],
    },
}


def get_current_slot():
    """Returnează slot-ul activ la momentul curent (ora României)."""
    now = timezone.localtime()
    hour = now.hour
    weekday = now.weekday()  # 0=Luni, 6=Duminică

    # Sâmbătă seara (18-24) sau Duminică dimineața târziu (0-02) → Weekend Party
    if (weekday == 5 and 18 <= hour <= 23) or (weekday == 6 and hour < 2):
        return ('weekend_party', SLOTS['weekend_party'])

    # Sâmbătă / Duminică dimineața (6-11) → Weekend Morning
    if weekday in (5, 6) and 6 <= hour < 11:
        return ('weekend_morning', SLOTS['weekend_morning'])

    # Intervalele zilnice (aceleași pentru weekday, și pentru restul de weekend)
    if 6 <= hour < 10:
        return ('morning', SLOTS['morning'])
    if 10 <= hour < 14:
        return ('focus', SLOTS['focus'])
    if 14 <= hour < 18:
        return ('afternoon', SLOTS['afternoon'])
    if 18 <= hour < 22:
        return ('evening', SLOTS['evening'])
    if hour >= 22 or hour < 2:
        return ('night', SLOTS['night'])
    return ('late_night', SLOTS['late_night'])


def get_radio_songs(limit=80):
    """Returnează (slot_id, slot_config, queryset_melodii) pentru slot-ul curent."""
    slot_id, slot = get_current_slot()
    qs = Song.objects.filter(is_active=True).select_related('genre', 'mood')

    filter_q = Q()
    if slot['genres']:
        filter_q |= Q(genre__slug__in=slot['genres'])
    if slot['moods']:
        filter_q |= Q(mood__slug__in=slot['moods'])

    filtered = qs.filter(filter_q) if (slot['genres'] or slot['moods']) else qs

    # Fallback: dacă slot-ul nu are suficiente melodii, extinde la tot catalogul
    if filtered.count() < 10:
        filtered = qs

    return slot_id, slot, filtered.order_by('?')[:limit]


def get_slot_display(slot, lang='ro'):
    """Returnează titlul afișabil al slot-ului conform limbii curente."""
    return slot['name_en'] if lang == 'en' else slot['name_ro']
