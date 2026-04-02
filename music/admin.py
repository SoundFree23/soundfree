from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Song, Genre, Mood, Playlist, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil abonament'
    fields = ('subscription_start', 'subscription_end', 'notes')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'is_active', 'is_staff', 'get_subscription_status', 'get_subscription_end']

    def get_subscription_status(self, obj):
        if hasattr(obj, 'profile'):
            status = obj.profile.subscription_status()
            labels = {'active': 'Activ', 'expired': 'Expirat', 'not_started': 'Nu a început', 'no_subscription': 'Fără abonament', 'staff': 'Staff'}
            return labels.get(status, status)
        return '-'
    get_subscription_status.short_description = 'Status abonament'

    def get_subscription_end(self, obj):
        if hasattr(obj, 'profile') and obj.profile.subscription_end:
            return obj.profile.subscription_end
        return '-'
    get_subscription_end.short_description = 'Expiră la'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


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
