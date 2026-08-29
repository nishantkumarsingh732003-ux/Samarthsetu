/**
 * Offline shell for SETU.
 *
 * Hand-written rather than generated: the citizen route has a hard JS budget and a PWA
 * plugin would spend it. Three rules only.
 *
 *   1. Navigations  — network first, fall back to the cached shell. A citizen who walks
 *                     into a dead spot still gets the app, and the page then reads its
 *                     last results from localStorage.
 *   2. Static assets — cache first. They are content-hashed, so a stale hit is correct.
 *   3. API calls     — never cached. An eligibility verdict must not be served stale;
 *                      results the citizen has already seen are kept by the page itself.
 */
const VERSION = "setu-v1";
const SHELL = [
  "/",
  "/manifest.webmanifest",
  "/icons/icon-192.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Never cache the API: a verdict is a decision, not a static asset.
  if (url.pathname.startsWith("/api/") || url.port === "8000") return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(VERSION).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => caches.match(request).then((hit) => hit ?? caches.match("/"))),
    );
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then(
        (hit) =>
          hit ??
          fetch(request).then((response) => {
            const copy = response.clone();
            caches.open(VERSION).then((cache) => cache.put(request, copy));
            return response;
          }),
      ),
    );
  }
});
