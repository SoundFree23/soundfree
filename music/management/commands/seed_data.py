from django.core.management.base import BaseCommand
from music.models import Genre, Mood, Song


class Command(BaseCommand):
    help = 'Adaugă date demo în baza de date'

    def handle(self, *args, **kwargs):
        # Genuri
        genres_data = [
            ('Ambient', 'ambient', '🌊'),
            ('Jazz Lounge', 'jazz-lounge', '🎷'),
            ('Pop Instrumental', 'pop-instrumental', '🎹'),
            ('Electronic Chill', 'electronic-chill', '🎧'),
            ('Acoustic', 'acoustic', '🎸'),
            ('Classical Modern', 'classical-modern', '🎻'),
            ('Café Music', 'cafe-music', '☕'),
            ('Upbeat Retail', 'upbeat-retail', '🛍️'),
        ]
        genres = {}
        for name, slug, icon in genres_data:
            g, _ = Genre.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon})
            genres[slug] = g
            self.stdout.write(f'Genre: {name}')

        # Mood-uri
        moods_data = [
            ('Relaxant', 'relaxant', '#06b6d4'),
            ('Energic', 'energic', '#f59e0b'),
            ('Romantic', 'romantic', '#ec4899'),
            ('Profesional', 'profesional', '#7c3aed'),
            ('Vesel', 'vesel', '#22c55e'),
            ('Misterios', 'misterios', '#6366f1'),
        ]
        moods = {}
        for name, slug, color in moods_data:
            m, _ = Mood.objects.get_or_create(slug=slug, defaults={'name': name, 'color': color})
            moods[slug] = m
            self.stdout.write(f'Mood: {name}')

        # Melodii demo (fără fișiere audio — pentru preview UI)
        songs_data = [
            ('Morning Breeze', 'SoundFree Studio', 'ambient', 'relaxant', 72, 214, True),
            ('Coffee Shop Tales', 'SoundFree Studio', 'cafe-music', 'relaxant', 88, 187, True),
            ('Urban Flow', 'SoundFree Studio', 'electronic-chill', 'energic', 110, 243, True),
            ('Gentle Strings', 'SoundFree Studio', 'classical-modern', 'romantic', 65, 198, True),
            ('Summer Vibes', 'SoundFree Studio', 'pop-instrumental', 'vesel', 120, 221, True),
            ('Late Night Jazz', 'SoundFree Studio', 'jazz-lounge', 'misterios', 95, 312, True),
            ('Forest Rain', 'SoundFree Studio', 'ambient', 'relaxant', 60, 278, False),
            ('Acoustic Sunrise', 'SoundFree Studio', 'acoustic', 'vesel', 85, 195, False),
            ('Business Class', 'SoundFree Studio', 'electronic-chill', 'profesional', 105, 256, False),
            ('Sweet Harmony', 'SoundFree Studio', 'pop-instrumental', 'romantic', 118, 204, False),
            ('Deep Blue', 'SoundFree Studio', 'ambient', 'misterios', 70, 334, False),
            ('Retail Rush', 'SoundFree Studio', 'upbeat-retail', 'energic', 125, 183, False),
        ]

        for title, artist, genre_slug, mood_slug, bpm, duration, featured in songs_data:
            if not Song.objects.filter(title=title).exists():
                Song.objects.create(
                    title=title,
                    artist=artist,
                    genre=genres.get(genre_slug),
                    mood=moods.get(mood_slug),
                    bpm=bpm,
                    duration=duration,
                    is_featured=featured,
                    is_active=True,
                )
                self.stdout.write(f'Song: {title}')

        self.stdout.write(self.style.SUCCESS('\n✅ Date demo adăugate cu succes!'))
