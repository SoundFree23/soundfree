from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from .models import Song, Genre, Mood, Playlist, ContactMessage, UserProfile
from .forms import SongUploadForm, GenreForm


def is_staff(user):
    return user.is_staff


def get_or_create_profile(user):
    """Returnează profilul utilizatorului, creându-l dacă nu există."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def set_language(request, lang):
    if lang in ('ro', 'en'):
        request.session['lang'] = lang
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def user_login(request):
    error = None
    expired = False
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Staff users bypass subscription check
            if user.is_staff:
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            # Check subscription period
            profile = get_or_create_profile(user)
            if profile.is_subscription_active():
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                expired = True
        else:
            error = True
    return render(request, 'music/login.html', {
        'login_error': error,
        'subscription_expired': expired,
    })


def user_logout(request):
    logout(request)
    return redirect('/')


def home(request):
    total_songs = Song.objects.filter(is_active=True).count()
    context = {
        'total_songs': total_songs,
    }
    return render(request, 'music/home.html', context)


@login_required(login_url='/login/')
def library(request):
    if not request.user.is_staff:
        profile = get_or_create_profile(request.user)
        if not profile.is_subscription_active():
            return render(request, 'music/subscription_expired.html')
    return render(request, 'music/library.html')


def browse(request):
    songs = Song.objects.filter(is_active=True)
    genres = Genre.objects.all()
    moods = Mood.objects.all()
    featured_songs = Song.objects.filter(is_active=True, is_featured=True)[:8]
    recent_songs = Song.objects.filter(is_active=True).order_by('-id')[:8]

    genre_slug = request.GET.get('genre')
    mood_slug = request.GET.get('mood')
    search = request.GET.get('search', '')

    if genre_slug:
        songs = songs.filter(genre__slug=genre_slug)
    if mood_slug:
        songs = songs.filter(mood__slug=mood_slug)
    if search:
        songs = songs.filter(title__icontains=search)

    context = {
        'songs': songs,
        'genres': genres,
        'moods': moods,
        'featured_songs': featured_songs,
        'recent_songs': recent_songs,
        'current_genre': genre_slug,
        'current_mood': mood_slug,
        'search': search,
    }
    return render(request, 'music/browse.html', context)


@login_required(login_url='/login/')
def favorites(request):
    if not request.user.is_staff:
        profile = get_or_create_profile(request.user)
        if not profile.is_subscription_active():
            return render(request, 'music/subscription_expired.html')
    return render(request, 'music/favorites.html')


@login_required(login_url='/login/')
def playlist_detail(request, pl_id):
    if not request.user.is_staff:
        profile = get_or_create_profile(request.user)
        if not profile.is_subscription_active():
            return render(request, 'music/subscription_expired.html')
    return render(request, 'music/playlist_detail.html', {'pl_id': pl_id})


def pricing(request):
    return render(request, 'music/pricing.html')


def privacy(request):
    return render(request, 'music/privacy.html')


def terms(request):
    return render(request, 'music/terms.html')


def license_verify(request, token):
    from datetime import datetime
    profile = UserProfile.objects.filter(verification_token=token).select_related('user').first()
    if not profile:
        return render(request, 'music/verify_license.html', {'not_found': True})
    context = {
        'profile': profile,
        'username': profile.user.username,
        'status': profile.subscription_status(),
        'days_remaining': profile.days_remaining(),
        'subscription_start': profile.subscription_start,
        'subscription_end': profile.subscription_end,
        'verified_at': datetime.now(),
        'not_found': False,
    }
    return render(request, 'music/verify_license.html', context)


from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings

@require_POST
def contact_submit(request):
    name = request.POST.get('name', '')
    email = request.POST.get('email', '')
    business = request.POST.get('business', '')
    message = request.POST.get('message', '')
    try:
        ContactMessage.objects.create(
            name=name,
            email=email,
            business=business,
            message=message,
        )
    except Exception:
        pass
    try:
        send_mail(
            subject=f'[SoundFree] Contact: {name}',
            message=f'Nume: {name}\nEmail: {email}\nTip locatie: {business}\n\nMesaj:\n{message}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['office@soundfree.ro'],
            fail_silently=True,
        )
    except Exception:
        pass
    return JsonResponse({'ok': True})


def song_detail(request, pk):
    song = get_object_or_404(Song, pk=pk, is_active=True)
    Song.objects.filter(pk=pk).update(plays_count=song.plays_count + 1)
    related = Song.objects.filter(genre=song.genre, is_active=True).exclude(pk=pk)[:4]
    return render(request, 'music/song_detail.html', {'song': song, 'related': related})


def api_songs(request):
    songs = Song.objects.filter(is_active=True).select_related('genre').values(
        'id', 'title', 'audio_file', 'cover_image', 'duration',
        'genre__slug', 'genre__name'
    )
    songs_list = []
    for s in songs:
        songs_list.append({
            'id': s['id'],
            'title': s['title'],
            'artist': 'SoundFree',
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
        songs = songs.filter(title__icontains=search)
    return render(request, 'backend/songs.html', {'songs': songs, 'search': search})


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_upload(request):
    if request.method == 'POST':
        form = SongUploadForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save()
            # Auto-detect duration from audio file
            if song.audio_file:
                try:
                    from mutagen import File as MutagenFile
                    audio = MutagenFile(song.audio_file.path)
                    if audio and audio.info:
                        song.duration = int(audio.info.length)
                        song.save(update_fields=['duration'])
                except Exception:
                    pass
            # Auto-generate cover if none was uploaded
            if not song.cover_image:
                try:
                    from .cover_generator import auto_generate_cover
                    if auto_generate_cover(song):
                        messages.success(request, f'✅ Melodia „{song.title}" a fost încărcată cu succes! Copertă generată automat.')
                    else:
                        messages.success(request, f'✅ Melodia „{song.title}" a fost încărcată, dar coperta nu a putut fi generată.')
                except Exception:
                    messages.success(request, f'✅ Melodia „{song.title}" a fost încărcată cu succes!')
            else:
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


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_users(request):
    from datetime import datetime
    error = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            email = request.POST.get('email', '').strip()
            sub_start = request.POST.get('subscription_start', '').strip()
            sub_end = request.POST.get('subscription_end', '').strip()
            notes = request.POST.get('notes', '').strip()
            if username and password:
                if User.objects.filter(username=username).exists():
                    error = 'exists'
                else:
                    new_user = User.objects.create_user(username=username, password=password, email=email, is_staff=False)
                    profile = get_or_create_profile(new_user)
                    if sub_start:
                        profile.subscription_start = datetime.strptime(sub_start, '%Y-%m-%d').date()
                    if sub_end:
                        profile.subscription_end = datetime.strptime(sub_end, '%Y-%m-%d').date()
                    if notes:
                        profile.notes = notes
                    profile.save()
                    messages.success(request, '✅ Utilizator creat!')
                    return redirect('music:backend_users')
        elif action == 'update_subscription':
            user_id = request.POST.get('user_id')
            sub_start = request.POST.get('subscription_start', '').strip()
            sub_end = request.POST.get('subscription_end', '').strip()
            notes = request.POST.get('notes', '').strip()
            u = User.objects.filter(id=user_id, is_staff=False).first()
            if u:
                profile = get_or_create_profile(u)
                profile.subscription_start = datetime.strptime(sub_start, '%Y-%m-%d').date() if sub_start else None
                profile.subscription_end = datetime.strptime(sub_end, '%Y-%m-%d').date() if sub_end else None
                profile.notes = notes
                profile.save()
                messages.success(request, '✅ Abonament actualizat!')
            return redirect('music:backend_users')
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            User.objects.filter(id=user_id, is_staff=False).delete()
            return redirect('music:backend_users')
        elif action == 'toggle':
            user_id = request.POST.get('user_id')
            u = User.objects.filter(id=user_id, is_staff=False).first()
            if u:
                u.is_active = not u.is_active
                u.save()
            return redirect('music:backend_users')
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    # Ensure all users have profiles
    for u in users:
        get_or_create_profile(u)
    return render(request, 'backend/users.html', {'users': users, 'user_error': error})


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_user_playlists(request, user_id):
    target_user = get_object_or_404(User, id=user_id, is_staff=False)
    all_songs = Song.objects.filter(is_active=True).order_by('title')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_playlist':
            name = request.POST.get('name', '').strip()
            if name:
                Playlist.objects.create(name=name, user=target_user)
                messages.success(request, f'✅ Playlist "{name}" creat!')
                return redirect('music:backend_user_playlists', user_id=user_id)
        elif action == 'delete_playlist':
            pl_id = request.POST.get('playlist_id')
            Playlist.objects.filter(id=pl_id, user=target_user).delete()
            return redirect('music:backend_user_playlists', user_id=user_id)
        elif action == 'add_song':
            pl_id = request.POST.get('playlist_id')
            song_id = request.POST.get('song_id')
            pl = Playlist.objects.filter(id=pl_id, user=target_user).first()
            if pl and song_id:
                pl.songs.add(song_id)
            return redirect('music:backend_user_playlists', user_id=user_id)
        elif action == 'remove_song':
            pl_id = request.POST.get('playlist_id')
            song_id = request.POST.get('song_id')
            pl = Playlist.objects.filter(id=pl_id, user=target_user).first()
            if pl and song_id:
                pl.songs.remove(song_id)
            return redirect('music:backend_user_playlists', user_id=user_id)

    playlists = Playlist.objects.filter(user=target_user).prefetch_related('songs')
    return render(request, 'backend/user_playlists.html', {
        'target_user': target_user,
        'playlists': playlists,
        'all_songs': all_songs,
    })


@login_required(login_url='/backend/login/')
@user_passes_test(is_staff, login_url='/backend/login/')
def backend_messages(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        msg_id = request.POST.get('msg_id')
        if action == 'mark_read' and msg_id:
            ContactMessage.objects.filter(id=msg_id).update(is_read=True)
        elif action == 'mark_unread' and msg_id:
            ContactMessage.objects.filter(id=msg_id).update(is_read=False)
        elif action == 'delete' and msg_id:
            ContactMessage.objects.filter(id=msg_id).delete()
        return redirect('music:backend_messages')
    contact_messages = ContactMessage.objects.all()
    unread_count = contact_messages.filter(is_read=False).count()
    return render(request, 'backend/messages.html', {
        'contact_messages': contact_messages,
        'unread_count': unread_count,
    })


def api_user_playlists(request):
    """API: returns server-side playlists for the logged-in user"""
    if not request.user.is_authenticated:
        return JsonResponse({'playlists': []})
    playlists = Playlist.objects.filter(user=request.user).prefetch_related('songs')
    data = []
    for pl in playlists:
        songs = []
        for s in pl.songs.all():
            songs.append({
                'id': s.id,
                'title': s.title,
                'artist': 'SoundFree',
                'audio': s.audio_file.url if s.audio_file else '',
                'cover': s.cover_image.url if s.cover_image else '',
                'duration': s.duration,
            })
        data.append({
            'id': pl.id,
            'name': pl.name,
            'songs': songs,
            'count': len(songs),
        })
    return JsonResponse({'playlists': data})
