"""Views care servesc artefactele PWA de la rădăcina site-ului.

Service worker-ul TREBUIE să fie servit de la rădăcină (sau cu antetul
Service-Worker-Allowed) ca să poată controla întregul site, nu doar /static/.
"""
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, FileResponse, Http404


_STATIC_ROOT = Path(settings.BASE_DIR) / 'static'


def _read(name: str) -> bytes:
    p = _STATIC_ROOT / name
    if not p.exists():
        raise Http404(name)
    return p.read_bytes()


def service_worker(request):
    """Servit la /service-worker.js — scope = întregul site."""
    body = _read('service-worker.js')
    resp = HttpResponse(body, content_type='application/javascript')
    resp['Service-Worker-Allowed'] = '/'
    resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


def manifest(request):
    """Servit la /manifest.webmanifest."""
    body = _read('manifest.webmanifest')
    resp = HttpResponse(body, content_type='application/manifest+json')
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp


def offline(request):
    """Pagină simplă afișată când utilizatorul e complet offline și fără cache."""
    html = """<!doctype html>
<html lang="ro"><head><meta charset="utf-8">
<title>Offline — SoundFree</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{margin:0;background:#121212;color:#fff;font-family:Inter,system-ui,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:2rem}h1{color:#1db954;margin:0 0 .5rem}p{color:#b3b3b3}</style>
</head><body><div><h1>Offline</h1><p>Nicio conexiune. Reconectează-te ca să continui ascultarea.</p></div></body></html>"""
    return HttpResponse(html, content_type='text/html; charset=utf-8')
