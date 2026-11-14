// Service Worker der Seite «Handy-Funkgerät» (erzeugt von werkzeuge/funk_pwa.py): alles aus dem Speicher, damit die Seite
// nach dem ersten Laden ohne Internet geht. Eine neue Seite = ein neuer Name des Speichers (die alte wird gelöscht).
const C = 'funk-c4ee4e34b41d';
const TEILE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];
self.addEventListener('install', e => { e.waitUntil(caches.open(C).then(c => c.addAll(TEILE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k))))
  .then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const r = e.request; if (r.method !== 'GET' || new URL(r.url).origin !== self.location.origin) return;
  e.respondWith(caches.match(r, {ignoreSearch: true}).then(h => h || fetch(r).catch(() => r.mode === 'navigate' ? caches.match('index.html') : Response.error())));
});
