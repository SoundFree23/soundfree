from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'music'

urlpatterns = [
    # Site public
    path('', views.home, name='home'),
    path('library/', views.library, name='library'),
    path('browse/', views.browse, name='browse'),
    path('favorites/', views.favorites, name='favorites'),
    path('playlist/<str:pl_id>/', views.playlist_detail, name='playlist_detail'),
    path('pricing/', views.pricing, name='pricing'),
    path('song/<int:pk>/', views.song_detail, name='song_detail'),
    path('api/songs/', views.api_songs, name='api_songs'),
    path('lang/<str:lang>/', views.set_language, name='set_language'),

    # Backend admin
    path('backend/', views.backend_dashboard, name='backend_dashboard'),
    path('backend/songs/', views.backend_songs, name='backend_songs'),
    path('backend/upload/', views.backend_upload, name='backend_upload'),
    path('backend/song/<int:pk>/edit/', views.backend_edit_song, name='backend_edit_song'),
    path('backend/song/<int:pk>/delete/', views.backend_delete_song, name='backend_delete_song'),
    path('backend/song/<int:pk>/toggle/', views.backend_toggle_song, name='backend_toggle_song'),
    path('backend/genres/', views.backend_genres, name='backend_genres'),
    path('backend/login/', auth_views.LoginView.as_view(template_name='backend/login.html'), name='backend_login'),
    path('backend/logout/', auth_views.LogoutView.as_view(next_page='/backend/login/'), name='backend_logout'),
]
