from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from music.media_serve import serve_media_with_range
from music import pwa_views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(
        r'^media/(?P<path>.*)$',
        serve_media_with_range,
        {'document_root': settings.MEDIA_ROOT},
    ),
    # PWA — servite de la rădăcină ca service worker-ul să aibă scope = /
    path('service-worker.js', pwa_views.service_worker, name='pwa_service_worker'),
    path('manifest.webmanifest', pwa_views.manifest, name='pwa_manifest'),
    path('offline/', pwa_views.offline, name='pwa_offline'),
    path('', include('music.urls', namespace='music')),
]
