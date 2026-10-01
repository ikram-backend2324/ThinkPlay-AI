{% load static %}/* TeachX service worker — offline support.
 *
 * Pages: network first, falling back to the last cached copy, then to the
 * offline page. Static files and CDN libraries: served from cache and
 * refreshed in the background. Assigned tests, lectures and the SCAFFOLD
 * guide are pre-cached by the pages that list them (see "prefetch").
 */
const VERSION = "{{ version }}";
const STATIC_CACHE = `static-${VERSION}`;
const PAGE_CACHE = `pages-${VERSION}`;
const OFFLINE_URL = "{% url 'offline' %}";

const PRECACHE = [
  OFFLINE_URL,
  "{% static 'css/theme.css' %}",
  "{% static 'css/teachx.css' %}",
  "{% static 'js/app.js' %}",
  "{% static 'js/three-bg.js' %}",
  "{% static 'js/quiz-take.js' %}",
  "{% static 'icons/icon-192.png' %}",
  "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js",
  "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js",
  "https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js",
  "https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js",
];

// Never cache these: admin, auth flows and anything that changes server state.
const NEVER_CACHE = [/^\/admin\//, /^\/accounts\/(login|logout)\//, /^\/set-language\//, /^\/sw\.js$/];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) =>
      // One failing CDN file must not break installation.
      Promise.all(PRECACHE.map((url) => cache.add(url).catch(() => null)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== STATIC_CACHE && k !== PAGE_CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function isCacheablePage(url) {
  return url.origin === self.location.origin && !NEVER_CACHE.some((re) => re.test(url.pathname));
}

async function cachePage(request, response) {
  // A redirected response (e.g. to the login page) must not be stored under the original URL.
  if (response.ok && !response.redirected && response.type === "basic") {
    const cache = await caches.open(PAGE_CACHE);
    await cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    return await cachePage(request, response);
  } catch (err) {
    const cached = await caches.match(request, { ignoreVary: true });
    return cached || (await caches.match(OFFLINE_URL)) || Response.error();
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cached = await cache.match(request);
  const refresh = fetch(request)
    .then((response) => {
      if (response.ok || response.type === "opaque") cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);
  return cached || refresh;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);

  if (request.mode === "navigate") {
    if (isCacheablePage(url)) event.respondWith(networkFirst(request));
    return;
  }
  const isStatic = url.origin === self.location.origin && url.pathname.startsWith("/static/");
  const isCdn = ["cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com"].includes(url.hostname);
  if (isStatic || isCdn) event.respondWith(staleWhileRevalidate(request));
});

self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type === "clear-pages") {
    event.waitUntil(caches.delete(PAGE_CACHE));
  } else if (data.type === "prefetch" && Array.isArray(data.urls)) {
    event.waitUntil(
      Promise.all(
        data.urls.slice(0, 60).map((href) => {
          const url = new URL(href, self.location.origin);
          if (!isCacheablePage(url)) return null;
          const request = new Request(url.href, { credentials: "same-origin" });
          return fetch(request).then((response) => cachePage(request, response)).catch(() => null);
        })
      )
    );
  }
});
