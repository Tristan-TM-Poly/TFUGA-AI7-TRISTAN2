"use strict";

const CACHE = "tristan-web-os-r03-v5";
const SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./r03.css",
  "./oakgate.css",
  "./accessibility.css",
  "./app.js",
  "./app.webmanifest",
  "./src/application.js",
  "./src/data-store.js",
  "./src/exporters.js",
  "./src/oak-engine.js",
  "./src/preferences.js",
  "./src/router.js",
  "./src/search-engine.js",
  "./src/ui.js",
  "./src/views/about.js",
  "./src/views/atlas.js",
  "./src/views/claims.js",
  "./src/views/dashboard.js",
  "./src/views/evidence.js",
  "./src/views/graph.js",
  "./src/views/mminus.js",
  "./src/views/oakgate.js",
  "./src/views/provenance.js",
  "./src/views/roadmap.js",
  "./src/views/theory.js",
  "./data/theories.json",
  "./data/claims.json",
  "./data/relations.json",
  "./data/provenance.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  const isData = url.pathname.endsWith(".json");
  if (isData) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
      const clone = response.clone();
      caches.open(CACHE).then((cache) => cache.put(event.request, clone));
      return response;
    }))
  );
});
