from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from .models import Song, Genre, Mood, Playlist
from .forms import SongUploadForm, GenreForm


def is_staff(user):
    return user.is_staff


def set_language(request, lang):
    if lang in ('ro', 'en'):
        request.session['lang'] = lang
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def home(request):
    featured_songs = Song.objects.filter(is_active=True, is_featured=True)[:8]
    recent_songs = Song.objects.filter(is_active=True).order_by('-id')[:8]
    genres = Genre.objects.all()
    total_songs = Song.objects.filter(is_active=True).count()
    context = {
        'featured_songs': featured_songs,
        'recent_songs': recent_songs,
        'genres': genres,
        'total_songs': total_songs,
    }
    return render(request, 'music/home.html', context)


def library(request):
    return render(request, 'music/library.html')


def browse(request):
    songs = Song.objects.filter(is_active=True)
    genres = Genre.objects.all()
    moods = Mood.objects.all()

    genre_slug = request.GET.get('genre')
    mood_slug = request.GET.get('mood')
    search = request.GET.get('search', '')

    if genre_slug:
        songs = songs.filter(genre__slug=genre_slug)
    if mood_slug:
        songs = songs.filter(mood__slug=mood_slug)
    if search:
        songs = songs.filter(title__icontains=search) | songs.filter(artist__icontains=search)

    context = {
        'songs': songs,
        'genres': genres,
        'moods': moods,
        'current_genre': genre_slug,
        'current_mood': mood_slug,
        'search': search,
    }
    return render(request, 'music/browse.html', context)


def favorites(request):
    return render(request, 'music/favorites.html')


def playlist_detail(request, pl_id):
    return render(request, 'music/playlist_detail.html', {'pl_id': pl_id})


def pricing(request):
    return render(request, 'music/pricing.html')


def song_detail(request, pk):
    song = get_object_or_404(Song, pk=pk, is_active=True)
    Song.objects.filter(pk=pk).update(plays_count=song.plays_count + 1)
    related = Song.objects.filter(genre=song.genre, is_active=True).exclude(pk=pk)[:4]
    return render(request, 'music/song_detail.html', {'song': song, 'related': related})


def api_songs(request):
    songs = Song.objects.filter(is_active=True).select_related('genre').values(
        'id', 'title', 'artist', 'audio_file', 'cover_image', 'duration',
        'genre__slug', 'genre__name'
    )
    songs_list = []
    for s in songs:
        songs_list.append({
            'id': s['id'],
            'title': s['title'],
            'artist': s['artist'],
            'audio': request.build_absolute_uri(f"/media/{s['audio_file']}") if s['audio_file'] else '',
            'cover': request.build_absolute_uri(f"/media/{s['cover_image']}") if s['cover_image'] else '',
            'duration': s['duration'],
            'genre': s['genre__slug'] or '',
            'genre_name': s['genre__name'] or '',
        })
    return JsonResponse({'songs': songs_list})


# ─── PANEL ADMIN CUSTOM ───────────────────────────────────────────

@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_dashboard(request):
    total_songs = Song.objects.count()
    active_songs = Song.objects.filter(is_active=True).count()
    featured_songs = Song.objects.filter(is_featured=True).count()
    total_plays = Song.objects.aggregate(total=Sum('plays_count'))['total'] or 0
    recent_songs = Song.objects.order_by('-created_at')[:10]
    genres = Genre.objects.all()
    context = {
        'total_songs': total_songs,
        'active_songs': active_songs,
        'featured_songs': featured_songs,
        'total_plays': total_plays,
        'recent_songs': recent_songs,
        'genres': genres,
    }
    return render(request, 'backend/dashboard.html', context)


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_songs(request):
    search = request.GET.get('search', '')
    songs = Song.objects.select_related('genre', 'mood').order_by('-created_at')
    if search:
        songs = songs.filter(title__icontains=search) | songs.filter(artist__icontains=search)
    return render(request, 'backend/songs.html', {'songs': songs, 'search': search})


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_upload(request):
    if request.method == 'POST':
        form = SongUploadForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save()
            messages.success(request, f'✅ Melodia „{song.title}" a fost încărcată cu succes!')
            return redirect('music:backend_songs')
        else:
            messages.error(request, '❌ Eroare la încărcare. Verifică câmpurile obligatorii.')
    else:
        form = SongUploadForm(initial={'is_active': True})
    return render(request, 'backend/upload.html', {'form': form})


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_edit_song(request, pk):
    song = get_object_or_404(Song, pk=pk)
    if request.method == 'POST':
        form = SongUploadForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Melodia „{song.title}" a fost actualizată!')
            return redirect('music:backend_songs')
    else:
        form = SongUploadForm(instance=song)
    return render(request, 'backend/upload.html', {'form': form, 'song': song, 'editing': True})


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_delete_song(request, pk):
    song = get_object_or_404(Song, pk=pk)
    if request.method == 'POST':
        title = song.title
        song.delete()
        messages.success(request, f'🗑️ Melodia „{title}" a fost ștearsă.')
        return redirect('music:backend_songs')
    return render(request, 'backend/confirm_delete.html', {'song': song})


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_toggle_song(request, pk):
    song = get_object_or_404(Song, pk=pk)
    song.is_active = not song.is_active
    song.save()
    return redirect(request.META.get('HTTP_REFERER', '/backend/songs/'))


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_genres(request):
    if request.method == 'POST':
        form = GenreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Gen adăugat cu succes!')
            return redirect('music:backend_genres')
    else:
        form = GenreForm()
    genres = Genre.objects.all()
    return render(request, 'backend/genres.html', {'form': form, 'genres': genres})
