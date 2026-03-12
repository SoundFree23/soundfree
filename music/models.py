from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume gen")
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='🎵', verbose_name="Icon emoji")

    class Meta:
        verbose_name = "Gen muzical"
        verbose_name_plural = "Genuri muzicale"

    def __str__(self):
        return self.name


class Mood(models.Model):
    name = models.CharField(max_length=100, verbose_name="Stare/Mood")
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=20, default='#7c3aed', verbose_name="Culoare hex")

    class Meta:
        verbose_name = "Mood"
        verbose_name_plural = "Mood-uri"

    def __str__(self):
        return self.name


class Song(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titlu melodie")
    artist = models.CharField(max_length=200, verbose_name="Artist / Compozitor")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gen")
    mood = models.ForeignKey(Mood, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mood")
    audio_file = models.FileField(upload_to='songs/', verbose_name="Fișier audio (MP3/WAV)")
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True, verbose_name="Copertă")
    duration = models.PositiveIntegerField(default=0, verbose_name="Durată (secunde)")
    bpm = models.PositiveIntegerField(null=True, blank=True, verbose_name="BPM")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    is_featured = models.BooleanField(default=False, verbose_name="Recomandat")
    plays_count = models.PositiveIntegerField(default=0, verbose_name="Redări")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Melodie"
        verbose_name_plural = "Melodii"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist}"

    def duration_display(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"


class Playlist(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nume playlist")
    description = models.TextField(blank=True, verbose_name="Descriere")
    songs = models.ManyToManyField(Song, blank=True, verbose_name="Melodii")
    cover_image = models.ImageField(upload_to='playlists/', null=True, blank=True)
    is_public = models.BooleanField(default=True, verbose_name="Public")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Playlist"
        verbose_name_plural = "Playlist-uri"

    def __str__(self):
        return self.name
