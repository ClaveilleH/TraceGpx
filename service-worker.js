const STATIC_CACHE = "tracegpx-static-v1";
const RUNTIME_CACHE = "tracegpx-runtime-v1";

const APP_SHELL = [
  "./tracegpx.html",
  "./manifest.webmanifest",
  "./tracegpx-icon.svg",
];

const CACHEABLE_ORIGINS = new Set([
  "https://cdnjs.cloudflare.com",
  "https://fonts.googleapis.com",
  "https://fonts.gstatic.com",
]);

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => ![STATIC_CACHE, RUNTIME_CACHE].includes(key))
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request, "./tracegpx.html"));
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(request));
    return;
  }

  if (isMapOrApiRequest(url)) return;

  if (CACHEABLE_ORIGINS.has(url.origin)) {
    event.respondWith(cacheFirst(request));
  }
});

function isMapOrApiRequest(url) {
  return url.hostname === "data.geopf.fr" ||
    url.hostname.endsWith(".tile.opentopomap.org");
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  if (response && (response.ok || response.type === "opaque")) {
    const cache = await caches.open(RUNTIME_CACHE);
    await cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      await cache.put(request, response.clone());
    }
    return response;
  } catch {
    return caches.match(request).then(cached => cached || caches.match(fallbackUrl));
  }
}
