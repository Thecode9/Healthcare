const CACHE_NAME = 'smarthealthplus-v1';
const urlsToCache = [
    '/',
    '/login/',
    '/dashboard/',
    '/symptoms/',
    '/history/',
    '/health-tips/',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
