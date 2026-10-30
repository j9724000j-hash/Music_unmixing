const CACHE = 'turkish-organ-v1-20261030';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './css/style.css',
  './js/audio-engine.js',
  './js/instruments.js',
  './js/rhythms.js',
  './js/maqam.js',
  './js/app.js'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));
});
self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
