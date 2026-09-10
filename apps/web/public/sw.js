/**
 * Offline shell for SamarthSetu.
 *
 * Hand-written rather than generated: the citizen route has a hard JS budget and a PWA
 * plugin would spend it.
 *
 *   1. Navigations   — network first, fall back to the cached shell. A citizen who walks
 *                      into a dead spot still gets the app, and the page then reads its
 *                      last results from localStorage.
 *   2. `/_next/static` — cache first. These filenames genuinely carry a content hash, so
 *                      a stale hit is impossible: a changed file is a changed URL.
 *   3. Other assets  — network first, cache as a fallback. Icons, the manifest and
 *                      anything else served under a *stable* name would otherwise be
 *                      pinned forever by a cache-first rule.
 *   4. API calls     — never cached. An eligibility verdict must not be served stale;
 *                      results the citizen has already seen are kept by the page itself.
 *
 * Rule 3 is a bug fix, and the bug was ugly. The previous version applied cache-first to
 * every same-origin GET, justified by "they are content-hashed, so a stale hit is
 * correct". That is true of `/_next/static` in a production build and false of everything
 * else — and completely false in development, where `next dev` serves
 * `/_next/static/chunks/webpack.js` with no hash at all. A browser that visited a dev
 * server once pinned that `webpack.js` forever, and every subsequent rebuild produced
 *
 *     TypeError: Cannot read properties of undefined (reading 'call')
 *
 * out of webpack.js, on a server that was serving correct files, with nothing in the
 * logs. The worker is also no longer registered in development at all — see
 * components/ServiceWorker.tsx, which now actively unregisters it and clears these
 * caches, so a browser already in that state heals on its next load.
 *
 * Bump VERSION when the caching rules change: `activate` deletes every cache that is not
 * the current one, which is what evicts a poisoned cache from a browser in the wild.
 */
const VERSION = "setu-v3";

const SHELL = ["/", "/manifest.webmanifest", "/icons/icon-192.svg"];

/** Only these are safe to serve cache-first: the filename contains a content hash. */
const IMMUTABLE = "/_next/static/";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(VERSION)
      // `addAll` rejects the whole install if any one entry 404s, which would leave the
      // worker permanently uninstalled over a missing icon. Each is added on its own.
      .then((cache) => Promise.all(SHELL.map((path) => cache.add(path).catch(() => {}))))
      .then(() => self.skipWaiting()),
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

/** Let the page tell the worker to stand down — used by the dev-mode cleanup. */
self.addEventListener("message", (event) => {
  if (event.data === "setu:purge") {
    event.waitUntil(caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k)))));
  }
});

function cachePut(request, response) {
  // Opaque and error responses must not be stored: caching a 404 makes it permanent.
  if (!response || !response.ok || response.type === "opaque") return response;
  const copy = response.clone();
  caches.open(VERSION).then((cache) => cache.put(request, copy));
  return response;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Never cache the API: a verdict is a decision, not a static asset.
  if (url.pathname.startsWith("/api/") || url.port === "8000") return;
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    // `respondWith` must be handed a Response. The previous version ended its offline
    // chain with `caches.match("/")`, which resolves to *undefined* when "/" is not in
    // the cache — and "/" is a middleware redirect into a locale, so `cache.add("/")` at
    // install is unreliable and its failure is swallowed. The browser then reported
    //
    //     TypeError: Failed to convert value to 'Response'
    //     The FetchEvent for "…" resulted in a network error response
    //
    // on every navigation, online as well as off, because the rejection happens after the
    // network attempt either way. Every branch below now ends in a real Response.
    event.respondWith(
      fetch(request)
        .then((response) => cachePut(request, response))
        .catch(async () => {
          const exact = await caches.match(request);
          if (exact) return exact;

          // The locale shell this navigation belongs to, then the bare root, then any
          // cached shell at all — a citizen offline on /hi/matches should still get the
          // Hindi shell rather than nothing.
          const url = new URL(request.url);
          const locale = url.pathname.split("/")[1];
          for (const path of [locale ? `/${locale}` : null, "/"]) {
            if (!path) continue;
            const shell = await caches.match(path);
            if (shell) return shell;
          }

          return new Response(
            "<!doctype html><meta charset=utf-8><title>Offline</title>" +
              "<p style=\"font:16px system-ui;padding:2rem\">You are offline, and this " +
              "page has not been opened on this device before. Reconnect and try again.</p>",
            { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } },
          );
        }),
    );
    return;
  }

  // Content-hashed: a cache hit is always the right file.
  if (url.pathname.startsWith(IMMUTABLE)) {
    event.respondWith(
      caches
        .match(request)
        .then((hit) => hit ?? fetch(request).then((response) => cachePut(request, response))),
    );
    return;
  }

  // Everything else lives at a stable URL and can change under it. The network wins when
  // it is there; the cache is what makes the app work when it is not.
  event.respondWith(
    fetch(request)
      .then((response) => cachePut(request, response))
      .catch(async () => {
        // Same rule as the navigation branch: a cache miss here resolves to `undefined`,
        // and `respondWith(undefined)` is a TypeError rather than a failed request. An
        // asset that was never cached and cannot be fetched is a plain 504.
        const hit = await caches.match(request);
        return hit ?? new Response("", { status: 504, statusText: "Offline" });
      }),
  );
});
