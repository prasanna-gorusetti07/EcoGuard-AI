// ECOGUARD AI - Service Worker
// Version: 1.0.0
// Capabilities: App Shell Caching, Offline Navigation, Network-First API Fallback

const CACHE_NAME = 'ecoguard-ai-v1';

const PRECACHE_ASSETS = [
    '/',
    '/manifest.json',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/citizen.js',
    '/static/js/officer.js',
    '/static/js/hotspots.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/icons/icon-192x192-maskable.png',
    '/static/icons/icon-512x512-maskable.png',
    '/static/icons/apple-touch-icon.png',
    '/static/icons/favicon.png',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

// Install: Precache App Shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        }).then(() => self.skipWaiting())
    );
});

// Activate: Clean up old cache versions
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Strategy depending on request type
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Non-GET requests (e.g. POST complaint upload) pass directly to network
    if (event.request.method !== 'GET') {
        return;
    }

    // 1. API Endpoints: Network-First with cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, copy);
                        });
                    }
                    return networkResponse;
                })
                .catch(() => {
                    return caches.match(event.request).then((cached) => {
                        if (cached) return cached;
                        return new Response(
                            JSON.stringify({ offline: true, message: 'You are currently offline. Displaying cached records.' }),
                            { headers: { 'Content-Type': 'application/json' }, status: 200 }
                        );
                    });
                })
        );
        return;
    }

    // 2. HTML Navigation requests: Network-First, fallback to cached '/'
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then((networkResponse) => {
                    return caches.open(CACHE_NAME).then((cache) => {
                        cache.put('/', networkResponse.clone());
                        return networkResponse;
                    });
                })
                .catch(() => {
                    return caches.match('/').then((cached) => {
                        return cached || new Response('<h1>EcoGuard AI (Offline)</h1><p>Please reconnect to the internet.</p>', {
                            headers: { 'Content-Type': 'text/html' }
                        });
                    });
                })
        );
        return;
    }

    // 3. Static Assets (CSS, JS, Icons, Images): Cache-First with Network fallback
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                // Fetch in background to revalidate cache (stale-while-revalidate)
                fetch(event.request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, networkResponse);
                        });
                    }
                }).catch(() => {});
                return cachedResponse;
            }

            return fetch(event.request).then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200) {
                    const copy = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, copy);
                    });
                }
                return networkResponse;
            });
        })
    );
});
