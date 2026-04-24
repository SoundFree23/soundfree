from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from music.media_serve import serve_media_with_range

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(
        r'^media/(?P<path>.*)$',
        serve_media_with_range,
        {'document_root': settings.MEDIA_ROOT},
    ),
    path('', include('music.urls', namespace='music')),
]
