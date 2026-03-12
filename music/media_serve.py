"""
Custom media file serving with HTTP Range request support.
Django's built-in dev server doesn't support Range requests,
which breaks audio/video seek (progress bar scrubbing).
"""
import os
import re
import mimetypes
from django.http import HttpResponse, FileResponse, Http404


def serve_media_with_range(request, path, document_root=None):
    """Serve media files with support for HTTP Range requests (byte-range)."""
    if document_root is None:
        raise Http404

    # Build full path and prevent directory traversal
    full_path = os.path.join(document_root, path)
    full_path = os.path.normpath(full_path)
    if not full_path.startswith(os.path.normpath(document_root)):
        raise Http404

    if not os.path.isfile(full_path):
        raise Http404

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    content_type = content_type or 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '')

    if range_header:
        # Parse Range header: "bytes=start-end"
        range_match = re.match(r'bytes=(\d*)-(\d*)', range_header)
        if range_match:
            start = range_match.group(1)
            end = range_match.group(2)

            start = int(start) if start else 0
            end = int(end) if end else file_size - 1

            # Clamp values
            start = max(0, start)
            end = min(end, file_size - 1)

            if start > end or start >= file_size:
                # Requested range not satisfiable
                response = HttpResponse(status=416)
                response['Content-Range'] = f'bytes */{file_size}'
                return response

            length = end - start + 1

            with open(full_path, 'rb') as f:
                f.seek(start)
                data = f.read(length)

            response = HttpResponse(data, status=206, content_type=content_type)
            response['Content-Length'] = length
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            return response

    # No Range header — serve full file, but advertise Range support
    response = FileResponse(open(full_path, 'rb'), content_type=content_type)
    response['Content-Length'] = file_size
    response['Accept-Ranges'] = 'bytes'
    return response
