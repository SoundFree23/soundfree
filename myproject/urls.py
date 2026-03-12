from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from music.media_serve import serve_media_with_range

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('music.urls', namespace='music')),
]

# In development, serve media files with Range request support (needed for audio seek)
if settings.DEBUG:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve_media_with_range,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
