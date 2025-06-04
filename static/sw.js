
        // QQ Universal Fullscreen App Experience Service Worker
        
        const CACHE_NAME = 'traxovo-app-v1';
        const urlsToCache = [
            '/',
            '/quantum-dashboard',
            '/fleet-map',
            '/attendance-matrix',
            '/asset-manager',
            '/static/manifest.json',
            '/static/css/app.css',
            '/static/js/app.js'
        ];
        
        // Install service worker
        self.addEventListener('install', (event) => {
            event.waitUntil(
                caches.open(CACHE_NAME)
                    .then((cache) => {
                        return cache.addAll(urlsToCache);
                    })
            );
        });
        
        // Fetch from cache
        self.addEventListener('fetch', (event) => {
            event.respondWith(
                caches.match(event.request)
                    .then((response) => {
                        // Return cached version or fetch from network
                        return response || fetch(event.request);
                    })
            );
        });
        
        // Update service worker
        self.addEventListener('activate', (event) => {
            event.waitUntil(
                caches.keys().then((cacheNames) => {
                    return Promise.all(
                        cacheNames.map((cacheName) => {
                            if (cacheName !== CACHE_NAME) {
                                return caches.delete(cacheName);
                            }
                        })
                    );
                })
            );
        });
        