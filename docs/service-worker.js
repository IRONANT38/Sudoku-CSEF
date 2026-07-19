const CACHE_NAME = "mr-sudoku-shell-v2";
const DATA_CACHE = "mr-sudoku-data-v1";
const APP_SHELL = [
    "./",
    "./index.html",
    "./style.css",
    "./board.js",
    "./sudoku.js",
    "./manifest.webmanifest",
    "./favicon.svg",
    "./icons/icon-192.png",
    "./icons/icon-512.png",
    "./icons/apple-touch-icon.png"
];

self.addEventListener("install", event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(key => ![CACHE_NAME, DATA_CACHE].includes(key)).map(key => caches.delete(key))
        ))
    );
    self.clients.claim();
});

self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== "GET" || url.origin !== self.location.origin) {
        return;
    }

    if (url.pathname.endsWith(".json.gz")) {
        event.respondWith(
            caches.open(DATA_CACHE).then(async cache => {
                const cached = await cache.match(request);

                if (cached) {
                    return cached;
                }

                const response = await fetch(request);

                if (response.ok) {
                    cache.put(request, response.clone());
                }

                return response;
            })
        );
        return;
    }

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request)
                .then(response => {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put("./index.html", copy));
                    return response;
                })
                .catch(() => caches.match("./index.html"))
        );
        return;
    }

    event.respondWith(
        caches.match(request).then(cached => cached || fetch(request).then(response => {
            if (response.ok) {
                caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
            }
            return response;
        }))
    );
});
