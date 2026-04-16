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

        # Melodiile demo au fost eliminate — doar genurile și mood-urile se mai seed-uiesc.

        self.stdout.write(self.style.SUCCESS('\n✅ Genuri și mood-uri demo adăugate cu succes!'))
