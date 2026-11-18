/* Offline support: app shell cached on install, fonts cached on first use.
   sr-v2 (2026-11-18): each page is cached under its own key. sr-v1 stored every page it
   navigated to as './index.html', so after visiting privacy.html the offline app opened
   the privacy page. Changing VERSION makes activate delete the sr-v1 cache.
   Only Cache Storage is touched here; localStorage (training records, settings) is not. */
const VERSION = 'sr-v2';
const SHELL = ['./', './index.html', './manifest.webmanifest', './privacy.html',
  './icons/icon-192.png', './icons/icon-512.png', './icons/maskable-512.png'];
const APP_KEY = './index.html', PRIVACY_KEY = './privacy.html';
const BASE = new URL('./', self.location.href);
const APP_PATHS = new Set([BASE.pathname, new URL(APP_KEY, BASE).pathname]);
const PRIVACY_PATH = new URL(PRIVACY_KEY, BASE).pathname;

// The cache key a page is stored under (query strings such as ?source=app are ignored).
function pageKey(url){
  if (APP_PATHS.has(url.pathname)) return APP_KEY;
  if (url.pathname === PRIVACY_PATH) return PRIVACY_KEY;
  return url.origin + url.pathname;
}

self.addEventListener('install', e => {
  // cache:'reload' skips the HTTP cache so the new version stores fresh copies.
  e.waitUntil(caches.open(VERSION)
    .then(c => c.addAll(SHELL.map(u => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Pages: network first so updates arrive, cache as fallback when offline.
  if (req.mode === 'navigate'){
    if (url.origin !== location.origin) return;
    const key = pageKey(url);
    e.respondWith(fetch(req).then(r => {
      // Only a normal, successful, same-origin page replaces the stored copy (no error pages, no redirects).
      if (r.ok && r.type === 'basic' && !r.redirected){
        const copy = r.clone(), saving = caches.open(VERSION).then(c => c.put(key, copy)).catch(() => {});
        try { e.waitUntil(saving); } catch(_){}
      }
      return r;
    }).catch(() => caches.open(VERSION).then(c => c.match(key)
      // An unknown page offline falls back to the app; the privacy page never does.
      .then(hit => hit || (key === PRIVACY_KEY ? offlinePage() : c.match(APP_KEY)))
      .then(hit => hit || offlinePage()))));
    return;
  }
  // Same-origin files and Google Fonts: cache first.
  if (url.origin === location.origin || /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)){
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
      if (r.ok || r.type === 'opaque'){ const copy = r.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return r;
    })));
  }
});
// Shown only when nothing usable is cached (for example, storage was cleared while offline).
function offlinePage(){
  return new Response('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>오프라인 · Offline</title><body style="font:16px/1.6 system-ui,sans-serif;margin:40px 24px">' +
    '<p>인터넷에 연결되어 있지 않아 이 페이지를 열 수 없습니다. 연결된 뒤 다시 열어 주세요.</p>' +
    '<p>You are offline and this page is not saved on this device. Please try again when you are connected.</p></body>',
    { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
