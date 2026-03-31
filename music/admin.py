from django.contrib import admin
from .models import Song, Genre, Mood, Playlist


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'mood', 'bpm', 'plays_count', 'is_active', 'is_featured', 'created_at']
    list_filter = ['genre', 'mood', 'is_active', 'is_featured']
    search_fields = ['title']
    list_editable = ['is_active', 'is_featured']
    readonly_fields = ['plays_count', 'created_at']
    fieldsets = (
        ('Informații melodie', {
            'fields': ('title', 'genre', 'mood', 'bpm')
        }),
        ('Fișiere', {
            'fields': ('audio_file', 'cover_image')
        }),
        ('Setări', {
            'fields': ('duration', 'is_active', 'is_featured', 'plays_count', 'created_at')
        }),
    )


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_public', 'created_at']
    filter_horizontal = ['songs']
