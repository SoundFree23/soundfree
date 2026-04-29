/* SoundFree PWA service worker.
 *
 * Strategy:
 *   - App shell (HTML): network-first, fall back to cache when offline.
 *   - Static assets (CSS/JS/fonts/icons): stale-while-revalidate.
 *   - /api/songs/ catalog: network-first (so new uploads show up).
 *   - /api/radio/, /api/radio/current/: network-only (auth + slot-sensitive).
 *   - /media/ audio files: BYPASS — partial Range responses break caching and seek.
 *   - POST/PUT/DELETE: never cache.
 *
 * Bump CACHE_VERSION whenever this file changes so old clients pick it up.
 */
const CACHE_VERSION = 'sf-v2';
const SHELL_CACHE   = `${CACHE_VERSION}-shell`;
const ASSET_CACHE   = `${CACHE_VERSION}-assets`;
const API_CACHE     = `${CACHE_VERSION}-api`;

const SHELL_URLS = [
  '/',
  '/browse/',
  '/library/',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png',
  '/static/manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_URLS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => !k.startsWith(CACHE_VERSION)).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

function isAudioRequest(url, req) {
  if (req.headers.has('range')) return true;
  if (url.pathname.startsWith('/media/')) return true;
  const ext = url.pathname.split('.').pop().toLowerCase();
  return ['mp3', 'm4a', 'aac', 'wav', 'flac', 'ogg', 'opus'].includes(ext);
}

function isStaticAsset(url) {
  if (url.pathname.startsWith('/static/')) return true;
  if (url.hostname === 'fonts.googleapis.com') return true;
  if (url.hostname === 'fonts.gstatic.com') return true;
  return false;
}

function isHTMLNavigation(req) {
  return req.mode === 'navigate' || (req.method === 'GET' && req.headers.get('accept')?.includes('text/html'));
}

async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) cache.put(req, fresh.clone()).catch(() => {});
    return fresh;
  } catch (_) {
    const cached = await cache.match(req);
    if (cached) return cached;
    if (isHTMLNavigation(req)) {
      const shell = await caches.match('/');
      if (shell) return shell;
    }
    throw _;
  }
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const networkPromise = fetch(req).then((res) => {
    if (res && res.ok) cache.put(req, res.clone()).catch(() => {});
    return res;
  }).catch(() => cached);
  return cached || networkPromise;
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Same origin only beyond this point (except google fonts handled by isStaticAsset)
  if (url.origin !== self.location.origin && !isStaticAsset(url)) return;

  // Audio: never touch — let the browser handle Range natively.
  if (isAudioRequest(url, req)) return;

  // Auth-sensitive radio API: pass through, don't cache.
  if (url.pathname.startsWith('/api/radio')) return;

  // Catalog API: network-first.
  if (url.pathname.startsWith('/api/songs')) {
    event.respondWith(networkFirst(req, API_CACHE));
    return;
  }

  // Static assets: stale-while-revalidate.
  if (isStaticAsset(url)) {
    event.respondWith(staleWhileRevalidate(req, ASSET_CACHE));
    return;
  }

  // HTML navigation: network-first with offline fallback.
  if (isHTMLNavigation(req)) {
    event.respondWith(networkFirst(req, SHELL_CACHE));
    return;
  }
});

self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
