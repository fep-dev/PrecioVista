// ============================================================
// PrecioVista — Service Worker (PWA offline)
// Copyright © 2026 PrecioVista. CC BY-NC-SA 4.0
// ============================================================

const CACHE_NAME = 'preciovista-v1';

// Se usa self.location para detectar el scope real en tiempo de ejecución
// Funciona tanto en localhost como en GitHub Pages (/preciovista/)
const BASE = self.location.pathname.replace(/\/sw\.js$/, '');

const ARCHIVOS_CACHE = [
  `${BASE}/index.html`,
  `${BASE}/css/styles.css`,
  `${BASE}/js/data.js`,
  `${BASE}/js/supabase.js`,
  `${BASE}/js/auth.js`,
  `${BASE}/js/app.js`,
  `${BASE}/pages/buscar.html`,
  `${BASE}/pages/comercio.html`,
  `${BASE}/pages/reportar.html`,
  `${BASE}/manifest.json`,
  `${BASE}/assets/logo.png`
];

// Instalar: cachear archivos estáticos
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ARCHIVOS_CACHE))
      .then(() => self.skipWaiting())
  );
});

// Activar: limpiar caches viejas
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: cache-first para estáticos, network-first para API
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Peticiones a Supabase: siempre red
  if (url.hostname.includes('supabase.co')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response('{}', { headers: { 'Content-Type': 'application/json' } })
      )
    );
    return;
  }

  // Solo manejar GET
  if (event.request.method !== 'GET') return;

  // Archivos estáticos: cache-first
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response && response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => caches.match(`${BASE}/index.html`));
    })
  );
});

// ✓ sw.js — completo
