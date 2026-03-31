from django import forms
from .models import Song, Genre, Mood, Playlist


class SongUploadForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'genre', 'mood', 'bpm', 'audio_file', 'cover_image', 'duration', 'is_featured', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'ex: Morning Breeze', 'class': 'form-input'}),
            'genre': forms.Select(attrs={'class': 'form-input'}),
            'mood': forms.Select(attrs={'class': 'form-input'}),
            'bpm': forms.NumberInput(attrs={'placeholder': 'ex: 90', 'class': 'form-input'}),
            'duration': forms.NumberInput(attrs={'placeholder': 'Durata în secunde (ex: 180)', 'class': 'form-input'}),
            'audio_file': forms.FileInput(attrs={'class': 'form-file', 'accept': 'audio/*'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check'}),
        }
        labels = {
            'title': 'Titlu melodie *',
            'genre': 'Gen muzical',
            'mood': 'Mood / Atmosferă',
            'bpm': 'BPM (tempo)',
            'audio_file': 'Fișier audio (MP3 / WAV) *',
            'cover_image': 'Copertă (JPG / PNG)',
            'duration': 'Durată (secunde)',
            'is_featured': 'Melodie recomandată (apare pe homepage)',
            'is_active': 'Activă (vizibilă în bibliotecă)',
        }


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'slug', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: Jazz Lounge'}),
            'slug': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: jazz-lounge'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: 🎷'}),
        }
